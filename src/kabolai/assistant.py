"""Main assistant orchestrator: record -> STT -> brain -> action -> TTS -> play."""

import logging
import threading
from typing import Optional

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


class Assistant:
    """Main assistant that orchestrates the voice pipeline."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.state = AssistantState(language=config.language)

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

        # TTS engines (lazy-load Ukrainian only when needed)
        logger.info("Initializing TTS engines...")
        self._tts_en = None
        self._tts_uk = None

    def _register_actions(self):
        """Import action modules so decorators register them."""
        import kabolai.actions.apps  # noqa: F401
        import kabolai.actions.system  # noqa: F401
        import kabolai.actions.web  # noqa: F401
        import kabolai.actions.media  # noqa: F401
        import kabolai.actions.conversation  # noqa: F401

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

    def process_utterance(self, audio_data) -> Optional[str]:
        """Full pipeline: audio -> text -> intent -> action -> response -> speech."""
        self.state.set_processing(True)
        try:
            return self._process(audio_data)
        finally:
            self.state.set_processing(False)

    def _process(self, audio_data) -> Optional[str]:
        lang = self.state.language

        # Step 1: STT
        if hasattr(self.stt, 'transcribe'):
            # VOSK engine supports language parameter
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

        # Step 2: Brain - parse intent
        brain_response = self.brain.process(user_text, lang)
        logger.info(
            f"[Brain] action={brain_response.command}, "
            f"conv={brain_response.is_conversation}, "
            f"resp='{brain_response.response_text[:80]}'"
        )

        # Step 3: Execute action (if any)
        response_text = brain_response.response_text

        if brain_response.command and not brain_response.is_conversation:
            action_result = registry.execute(
                brain_response.command.action,
                brain_response.command.params,
            )
            logger.info(
                f"[Action] {brain_response.command.action} -> "
                f"success={action_result.success}, msg='{action_result.message}'"
            )

            # Use action-provided speak text if available
            if action_result.success:
                speak = (
                    action_result.speak_text_uk if lang == "uk"
                    else action_result.speak_text_en
                )
                if speak:
                    response_text = speak

        # Step 4: TTS
        try:
            tts = self.tts_uk if lang == "uk" else self.tts_en
            speech = tts.synthesize(response_text)
            if speech.audio_data:
                if speech.format == "wav":
                    self.player.play_wav(speech.audio_data)
                else:
                    self.player.play_bytes(
                        speech.audio_data, speech.sample_rate
                    )
        except Exception as e:
            logger.error(f"[TTS] Error: {e}", exc_info=True)

        return response_text

    def speak(self, text: str, lang: str = None):
        """Speak text in the specified or current language."""
        lang = lang or self.state.language
        try:
            tts = self.tts_uk if lang == "uk" else self.tts_en
            speech = tts.synthesize(text)
            if speech.audio_data:
                if speech.format == "wav":
                    self.player.play_wav(speech.audio_data)
                else:
                    self.player.play_bytes(speech.audio_data, speech.sample_rate)
        except Exception as e:
            logger.error(f"[TTS] Speak error: {e}")

    def check_brain(self) -> bool:
        """Check if the LLM brain is available."""
        return self.brain.is_available()

    def shutdown(self):
        """Clean up all resources."""
        logger.info("Shutting down assistant...")
        self.state.shutdown()
        self.stt.cleanup()
        if self._tts_en:
            self._tts_en.cleanup()
        if self._tts_uk:
            self._tts_uk.cleanup()
        self.brain.cleanup()
        self.recorder.cleanup()
        logger.info("Assistant shut down.")
