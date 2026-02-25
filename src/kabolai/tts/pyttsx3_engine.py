"""pyttsx3-based TTS for English with thread-safe timeout protection.

pyttsx3 uses Windows COM objects (SAPI5) which are apartment-threaded.
Calling runAndWait() from daemon threads can deadlock. This module runs
pyttsx3 in its own dedicated thread to avoid COM threading issues.
"""

import logging
import queue
import tempfile
import threading
from pathlib import Path

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)

# Maximum seconds to wait for TTS synthesis
TTS_TIMEOUT = 15


class Pyttsx3TTS(TTSEngine):
    """English TTS using pyttsx3 (Windows SAPI5 / espeak).

    Runs pyttsx3 in a dedicated daemon thread to prevent COM deadlocks
    when called from other threads.
    """

    def __init__(self, rate: int = 175, volume: float = 0.9):
        self._rate = rate
        self._volume = volume
        # Task queue: (text, tmp_path, result_queue)
        self._task_queue = queue.Queue()
        self._running = True
        self._ready = threading.Event()
        # Start dedicated pyttsx3 thread
        self._thread = threading.Thread(
            target=self._engine_loop, daemon=True, name="pyttsx3-worker"
        )
        self._thread.start()
        # Wait for engine to initialize (max 10s)
        if not self._ready.wait(timeout=10):
            raise TTSError("pyttsx3 engine failed to initialize within 10s")

    def _engine_loop(self):
        """Dedicated thread for pyttsx3 — keeps COM in one apartment."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            self._engine = engine
            self._ready.set()
            logger.info("pyttsx3 engine thread started.")
        except Exception as e:
            logger.error(f"pyttsx3 init failed: {e}")
            self._ready.set()  # Unblock __init__ so it can raise
            return

        while self._running:
            try:
                task = self._task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            text, tmp_path, result_q = task
            try:
                engine.save_to_file(text, tmp_path)
                engine.runAndWait()
                wav_data = Path(tmp_path).read_bytes()
                Path(tmp_path).unlink(missing_ok=True)
                result_q.put(("ok", wav_data))
            except Exception as e:
                Path(tmp_path).unlink(missing_ok=True)
                result_q.put(("error", str(e)))

        try:
            engine.stop()
        except Exception:
            pass

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize text to WAV audio bytes (thread-safe, with timeout)."""
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        # Create temp file for pyttsx3 output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        result_q = queue.Queue()
        self._task_queue.put((text, tmp_path, result_q))

        # Wait with timeout — prevents infinite hang
        try:
            status, data = result_q.get(timeout=TTS_TIMEOUT)
        except queue.Empty:
            Path(tmp_path).unlink(missing_ok=True)
            logger.error(f"pyttsx3 timed out after {TTS_TIMEOUT}s")
            raise TTSError(f"TTS synthesis timed out after {TTS_TIMEOUT}s")

        if status == "error":
            raise TTSError(f"pyttsx3 synthesis failed: {data}")

        return SpeechResult(audio_data=data, sample_rate=22050, format="wav")

    def get_available_voices(self) -> list:
        if hasattr(self, '_engine'):
            voices = self._engine.getProperty("voices")
            return [v.id for v in voices] if voices else []
        return []

    def set_voice(self, voice_id: str) -> None:
        if hasattr(self, '_engine'):
            self._engine.setProperty("voice", voice_id)

    def set_speed(self, speed: float) -> None:
        # speed 1.0 = 175 wpm
        if hasattr(self, '_engine'):
            self._engine.setProperty("rate", int(175 * speed))

    def cleanup(self) -> None:
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=3)
