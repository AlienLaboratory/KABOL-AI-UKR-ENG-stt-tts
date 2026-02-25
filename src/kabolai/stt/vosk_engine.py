"""VOSK-based speech-to-text engine."""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from kabolai.core.exceptions import STTError, ModelNotFoundError
from kabolai.stt.base import STTEngine, TranscriptionResult

logger = logging.getLogger(__name__)


class VoskSTT(STTEngine):
    """VOSK offline speech recognition engine."""

    def __init__(self):
        self._models: dict = {}  # lang -> vosk.Model
        self._recognizers: dict = {}  # lang -> vosk.KaldiRecognizer
        self._sample_rate = 16000

    def load_model(self, model_path: str, language: str = "en") -> None:
        """Load a VOSK model for a specific language."""
        try:
            from vosk import Model, KaldiRecognizer, SetLogLevel
            SetLogLevel(-1)  # Suppress VOSK logging
        except ImportError:
            raise STTError("vosk package not installed. Run: pip install vosk")

        path = Path(model_path)
        if not path.exists():
            raise ModelNotFoundError(
                f"VOSK model not found at {path}. "
                f"Run: python scripts/download_models.py --profile cpu"
            )

        logger.info(f"Loading VOSK model for '{language}' from {path}")
        model = Model(str(path))
        recognizer = KaldiRecognizer(model, self._sample_rate)
        recognizer.SetWords(True)

        self._models[language] = model
        self._recognizers[language] = recognizer
        logger.info(f"VOSK model for '{language}' loaded successfully.")

    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio using the loaded VOSK model."""
        lang = language or next(iter(self._recognizers), "en")
        recognizer = self._recognizers.get(lang)

        if recognizer is None:
            raise STTError(f"No VOSK model loaded for language '{lang}'")

        # Ensure int16 format
        if audio_data.dtype != np.int16:
            if audio_data.dtype in (np.float32, np.float64):
                audio_data = (audio_data * 32767).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)

        audio_bytes = audio_data.tobytes()

        # Feed audio in chunks
        chunk_size = 4000 * 2  # 4000 samples * 2 bytes per sample
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i : i + chunk_size]
            recognizer.AcceptWaveform(chunk)

        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "").strip()

        # Reset recognizer for next utterance
        recognizer.Reset()

        return TranscriptionResult(
            text=text,
            language=lang,
            confidence=1.0 if text else 0.0,
            is_final=True,
        )

    def supports_language(self, lang_code: str) -> bool:
        return lang_code in self._recognizers

    def cleanup(self) -> None:
        self._recognizers.clear()
        self._models.clear()
