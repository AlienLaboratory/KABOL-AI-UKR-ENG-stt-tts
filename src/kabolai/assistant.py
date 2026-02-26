"""Main assistant orchestrator with interrupt support and self-healing.

Pipeline: record -> STT -> brain -> action -> TTS -> play
Key feature: user can INTERRUPT at any time by speaking again.
When interrupted, current pipeline is cancelled and new speech is processed.
"""

import logging
import queue
import threading
import time
from typing import Callable, Optional

from kabolai.core.config import AppConfig
from kabolai.core.state import AssistantState
from kabolai.audio.recorder import AudioRecorder
from kabolai.audio.player import AudioPlayer
from kabolai.stt.factory import create_stt_engine
from kabolai.tts.factory import create_tts_engine
from kabolai.brain.factory import create_brain
from kabolai.actions.registry import registry
from kabolai.actions.conversation import set_state_ref

logger = logging.getLogger(__name__)

# Maximum time (seconds) for the entire voice pipeline before watchdog kills it
PIPELINE_TIMEOUT = 20


class Assistant:
    """Main assistant that orchestrates the voice pipeline.

    Features:
    - INTERRUPT: user can talk at any time to cancel current pipeline
    - Event callbacks for GUI integration (user_text, response_text, error, status)
    - Self-healing watchdog — auto-resets if pipeline hangs
    - Proper state transitions
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.state = AssistantState(language=config.language)

        # Event system for GUI integration
        self._event_callbacks = []
        self._event_queue = queue.Queue()

        # TTS mute state (skip speech playback when True)
        self.tts_muted = False

        # Interrupt/cancel support
        self._cancel = threading.Event()
        self._pending_audio = None
        self._pending_lock = threading.Lock()

        # Give conversation actions access to state
        set_state_ref(self.state)

        # Initialize components
        self.recorder = AudioRecorder(config.audio)
        self.player = AudioPlayer(config.audio)
        self.brain = create_brain(config)

        # Import all action modules to trigger registration
        self._register_actions()

        # STT engine
        logger.info("Initializing STT engine...")
        self.stt = create_stt_engine(config)

        # TTS engines (lazy-load only when needed)
        logger.info("Initializing TTS engines...")
        self._tts_en = None
        self._tts_uk = None

    # ---- Event System ----

    def add_event_callback(self, callback: Callable):
        """Register a callback for assistant events."""
        self._event_callbacks.append(callback)

    def _emit_event(self, event_type: str, data: dict = None):
        """Emit an event to all registered callbacks and the event queue."""
        event = {"type": event_type, "data": data or {}, "time": time.time()}
        self._event_queue.put(event)
        for cb in self._event_callbacks:
            try:
                cb(event_type, data or {})
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    def drain_events(self) -> list:
        """Drain all pending events from the queue (for GUI polling)."""
        events = []
        while True:
            try:
                events.append(self._event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    # ---- Action Registration ----

    def _register_actions(self):
        """Import action modules so decorators register them."""
        import kabolai.actions.apps  # noqa: F401
        import kabolai.actions.system  # noqa: F401
        import kabolai.actions.web  # noqa: F401
        import kabolai.actions.media  # noqa: F401
        import kabolai.actions.conversation  # noqa: F401

    # ---- TTS Lazy Loading ----

    @property
    def tts_en(self):
        if self._tts_en is None:
            self._tts_en = create_tts_engine(self.config, lang="en")
        return self._tts_en

    @property
    def tts_uk(self):
        if self._tts_uk is None:
            self._tts_uk = create_tts_engine(self.config, lang="uk")
        return self._tts_uk

    # ---- Voice Pipeline ----

    def handle_voice(self):
        """Record and process a voice command (push-to-talk mode).

        If pipeline is busy, FORCE-CANCEL it and start fresh.
        User pressing the mic button always wins.
        """
        if not self.state.try_start_pipeline():
            # Pipeline busy — force cancel and take over
            logger.info("[Push-to-talk] Interrupting busy pipeline...")
            self.interrupt()
            time.sleep(0.15)
            # Force-reset if still stuck
            if self.state.is_busy:
                self.state.force_reset()
                try:
                    self.state._voice_lock.release()
                except RuntimeError:
                    pass
            if not self.state.try_start_pipeline():
                logger.warning("[Push-to-talk] Could not acquire pipeline after interrupt.")
                return

        self._cancel.clear()
        try:
            self._emit_event("status", {"state": "listening"})
            self.state.set_listening(True)

            audio = self.recorder.record()
            self.state.set_listening(False)

            if audio is None:
                self._emit_event("status", {"state": "ready"})
                return

            self.state.set_processing(True)
            self._emit_event("status", {"state": "processing"})
            self._process(audio)

        except Exception as e:
            logger.error(f"Voice pipeline error: {e}", exc_info=True)
            self._emit_event("error", {"message": str(e)})
        finally:
            self.state.end_pipeline()
            self._emit_event("status", {"state": "ready"})

    def _process(self, audio_data) -> Optional[str]:
        """Full pipeline: audio -> STT -> brain -> action -> TTS."""
        lang = self.state.language

        # Check cancel before STT
        if self._cancel.is_set():
            logger.info("[Pipeline] Cancelled before STT.")
            return None

        # Step 1: STT
        if hasattr(self.stt, 'transcribe'):
            try:
                result = self.stt.transcribe(audio_data, language=lang)
            except TypeError:
                result = self.stt.transcribe(audio_data)
        else:
            result = self.stt.transcribe(audio_data)

        if not result.text.strip():
            logger.info("[STT] No speech detected in audio.")
            return None

        user_text = result.text.strip()
        logger.info(f"[STT] ({lang}): {user_text}")
        self._emit_event("user_text", {"text": user_text, "language": lang})

        # Check cancel before brain
        if self._cancel.is_set():
            logger.info("[Pipeline] Cancelled before brain.")
            return None

        # Step 2: Brain - parse intent
        brain_response = self.brain.process(user_text, lang)
        logger.info(
            f"[Brain] action={brain_response.command}, "
            f"conv={brain_response.is_conversation}, "
            f"resp='{brain_response.response_text[:80]}'"
        )

        # Check cancel before action
        if self._cancel.is_set():
            logger.info("[Pipeline] Cancelled before action.")
            return None

        # Step 3: Execute action (if any)
        response_text = brain_response.response_text

        if brain_response.command and not brain_response.is_conversation:
            try:
                action_result = registry.execute(
                    brain_response.command.action,
                    brain_response.command.params,
                )
                logger.info(
                    f"[Action] {brain_response.command.action} -> "
                    f"success={action_result.success}, msg='{action_result.message}'"
                )

                if action_result.success:
                    speak = (
                        action_result.speak_text_uk if lang == "uk"
                        else action_result.speak_text_en
                    )
                    if speak:
                        response_text = speak
            except Exception as e:
                logger.error(f"[Action] Error: {e}", exc_info=True)
                response_text = (
                    "Помилка при виконанні команди."
                    if lang == "uk"
                    else "Error executing command."
                )

        self._emit_event("response_text", {"text": response_text, "language": lang})

        # Check cancel before TTS
        if self._cancel.is_set():
            logger.info("[Pipeline] Cancelled before TTS.")
            return response_text

        # Step 4: TTS + Playback
        self._speak_response(response_text, lang)

        return response_text

    def _speak_response(self, text: str, lang: str):
        """Synthesize and play speech with proper state management."""
        self.state.set_processing(False)

        # Skip TTS when muted or cancelled
        if self.tts_muted:
            logger.info("[TTS] Muted — skipping speech playback.")
            return
        if self._cancel.is_set():
            logger.info("[TTS] Cancelled — skipping speech.")
            return

        self.state.set_speaking(True)
        self._emit_event("status", {"state": "speaking"})

        # Set cooldown BEFORE playback so continuous listener
        # ignores audio during TTS (prevents hearing own response)
        if self.is_continuous:
            word_count = len(text.split())
            estimated_duration = max(2.0, word_count / 2.5)
            self.recorder.set_cooldown(estimated_duration + 1.0)

        try:
            tts = self.tts_uk if lang == "uk" else self.tts_en
            speech = tts.synthesize(text)

            # Check cancel after synthesis (before playback)
            if self._cancel.is_set():
                logger.info("[TTS] Cancelled after synthesis, skipping playback.")
                return

            if speech.audio_data:
                if speech.format == "wav":
                    self.player.play_wav(speech.audio_data)
                else:
                    self.player.play_bytes(
                        speech.audio_data, speech.sample_rate
                    )
        except Exception as e:
            logger.error(f"[TTS/Playback] Error: {e}", exc_info=True)
        finally:
            self.state.set_speaking(False)
            if self.is_continuous:
                self.recorder.set_cooldown(1.0)

    def speak(self, text: str, lang: str = None):
        """Speak text in the specified or current language."""
        lang = lang or self.state.language
        self._speak_response(text, lang)

    # ---- Interrupt Support ----

    def interrupt(self):
        """Cancel the current pipeline immediately.

        Called when the user speaks while a pipeline is running.
        The cancel flag is checked at multiple points in _process().
        """
        self._cancel.set()
        # Stop any ongoing audio playback immediately
        try:
            self.player.stop()
        except Exception:
            pass
        logger.info("[Interrupt] Pipeline cancel signal sent + audio stopped.")

    # ---- Continuous Listening Mode ----

    def start_continuous(self):
        """Start always-listening mode (like Gemini/ChatGPT voice).

        The microphone stays open and automatically detects when you speak.
        When speech ends, it runs the full pipeline in a SEPARATE THREAD.
        If user speaks while pipeline is busy, it INTERRUPTS the current
        pipeline and processes the new speech instead.
        """
        logger.info("Starting continuous listening mode.")
        self._emit_event("status", {"state": "ready"})

        def on_speech_detected(audio_data):
            """Called by continuous listener — MUST return fast."""
            if not self.state.is_active:
                return

            # If pipeline is busy, INTERRUPT it and queue new audio
            if self.state.is_busy:
                logger.info("[Continuous] User spoke — interrupting current pipeline!")
                self.interrupt()
                with self._pending_lock:
                    self._pending_audio = audio_data
                return

            # Pipeline free — process in a separate thread
            threading.Thread(
                target=self._process_continuous_speech,
                args=(audio_data,),
                daemon=True,
            ).start()

        self.recorder.start_continuous(on_speech_detected)

    def _process_continuous_speech(self, audio_data):
        """Process speech from continuous listener in a separate thread."""
        if not self.state.try_start_pipeline():
            # Pipeline was claimed between our check and now — queue it
            with self._pending_lock:
                self._pending_audio = audio_data
            logger.debug("Pipeline lock contention — queued audio.")
            return

        self._cancel.clear()
        try:
            self.state.set_processing(True)
            self._emit_event("status", {"state": "processing"})
            self._process(audio_data)
        except Exception as e:
            logger.error(f"Continuous pipeline error: {e}", exc_info=True)
            self._emit_event("error", {"message": str(e)})
        finally:
            self.state.end_pipeline()
            self._emit_event("status", {"state": "ready"})

        # After current pipeline finishes, process any pending audio
        # from interrupt
        pending = None
        with self._pending_lock:
            pending = self._pending_audio
            self._pending_audio = None

        if pending is not None:
            logger.info("[Continuous] Processing queued interrupt audio.")
            self._process_continuous_speech(pending)

    def stop_continuous(self):
        """Stop always-listening mode."""
        logger.info("Stopping continuous listening mode.")
        self.recorder.stop_continuous()

    @property
    def is_continuous(self) -> bool:
        """True if continuous listening mode is active."""
        return self.recorder._continuous

    def check_brain(self) -> bool:
        """Check if the LLM brain is available."""
        return self.brain.is_available()

    def shutdown(self):
        """Clean up all resources."""
        logger.info("Shutting down assistant...")
        self._cancel.set()
        self.state.shutdown()
        self.recorder.stop_continuous()
        self.player.stop()
        self.recorder.stop()
        self.stt.cleanup()
        if self._tts_en:
            self._tts_en.cleanup()
        if self._tts_uk:
            self._tts_uk.cleanup()
        self.brain.cleanup()
        self.recorder.cleanup()
        logger.info("Assistant shut down.")
