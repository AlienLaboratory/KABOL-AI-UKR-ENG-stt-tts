"""pyttsx3-based TTS for English (CPU fallback using Windows SAPI5)."""

import io
import logging
import tempfile
from pathlib import Path

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)


class Pyttsx3TTS(TTSEngine):
    """English TTS using pyttsx3 (Windows SAPI5 / espeak)."""

    def __init__(self, rate: int = 175, volume: float = 0.9):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", rate)
            self._engine.setProperty("volume", volume)
        except Exception as e:
            raise TTSError(f"Failed to initialize pyttsx3: {e}") from e

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize text to WAV audio bytes."""
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        try:
            # pyttsx3 can save to file, then we read back
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            self._engine.save_to_file(text, tmp_path)
            self._engine.runAndWait()

            wav_data = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)

            return SpeechResult(audio_data=wav_data, sample_rate=22050, format="wav")
        except Exception as e:
            raise TTSError(f"pyttsx3 synthesis failed: {e}") from e

    def get_available_voices(self) -> list[str]:
        voices = self._engine.getProperty("voices")
        return [v.id for v in voices] if voices else []

    def set_voice(self, voice_id: str) -> None:
        self._engine.setProperty("voice", voice_id)

    def set_speed(self, speed: float) -> None:
        # speed 1.0 = 175 wpm
        self._engine.setProperty("rate", int(175 * speed))

    def cleanup(self) -> None:
        try:
            self._engine.stop()
        except Exception:
            pass
