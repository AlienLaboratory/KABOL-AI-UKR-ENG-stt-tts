"""faster-whisper based speech-to-text engine (optional GPU)."""

import logging
from typing import Optional

import numpy as np

from kabolai.core.exceptions import STTError
from kabolai.stt.base import STTEngine, TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperSTT(STTEngine):
    """faster-whisper GPU speech recognition engine."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cuda",
        compute_type: str = "float16",
    ):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    def load_model(self, model_path: str = None) -> None:
        """Load faster-whisper model. model_path is ignored (uses model_size)."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise STTError(
                "faster-whisper not installed. Run: pip install faster-whisper"
            )

        logger.info(
            f"Loading Whisper model '{self._model_size}' "
            f"on {self._device} ({self._compute_type})"
        )
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        logger.info("Whisper model loaded successfully.")

    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio using faster-whisper."""
        if self._model is None:
            raise STTError("Whisper model not loaded. Call load_model() first.")

        # faster-whisper expects float32 normalized audio
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype in (np.float32, np.float64):
            audio_float = audio_data.astype(np.float32)
        else:
            audio_float = audio_data.astype(np.float32)

        # Map language codes
        whisper_lang = {"en": "en", "uk": "uk"}.get(language)

        segments, info = self._model.transcribe(
            audio_float,
            language=whisper_lang,
            beam_size=5,
        )

        text = " ".join(seg.text.strip() for seg in segments)
        detected_lang = info.language if info else language

        return TranscriptionResult(
            text=text,
            language=detected_lang,
            confidence=info.language_probability if info else 0.0,
            is_final=True,
        )

    def supports_language(self, lang_code: str) -> bool:
        return lang_code in ("en", "uk")

    def cleanup(self) -> None:
        self._model = None
