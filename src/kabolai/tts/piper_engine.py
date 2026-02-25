"""Piper TTS engine for English (GPU profile, optional)."""

import logging
import subprocess
import tempfile
from pathlib import Path

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)


class PiperTTS(TTSEngine):
    """English TTS using piper-tts (local, fast, GPU-friendly)."""

    def __init__(self, model: str = "en_US-lessac-medium", model_path: str = None):
        self._model_name = model
        self._model_path = model_path
        self._piper = None
        self._initialize()

    def _initialize(self):
        """Initialize piper-tts."""
        try:
            # piper-tts provides a Python API
            from piper import PiperVoice

            if self._model_path and Path(self._model_path).exists():
                model_file = Path(self._model_path)
                onnx_files = list(model_file.glob("*.onnx"))
                if onnx_files:
                    self._piper = PiperVoice.load(str(onnx_files[0]))
                    logger.info(f"Piper TTS loaded: {onnx_files[0].name}")
                    return

            logger.warning(
                f"Piper model not found at {self._model_path}. "
                "Falling back to pyttsx3 if needed."
            )
        except ImportError:
            raise TTSError(
                "piper-tts not installed. Run: pip install piper-tts"
            )
        except Exception as e:
            raise TTSError(f"Failed to initialize Piper TTS: {e}") from e

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize text to WAV audio."""
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        if self._piper is None:
            raise TTSError("Piper model not loaded.")

        try:
            import io
            import wave

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav:
                self._piper.synthesize(text, wav)

            wav_data = wav_buffer.getvalue()
            return SpeechResult(audio_data=wav_data, sample_rate=22050, format="wav")
        except Exception as e:
            raise TTSError(f"Piper TTS synthesis failed: {e}") from e

    def get_available_voices(self) -> list[str]:
        return [self._model_name]

    def cleanup(self) -> None:
        self._piper = None
