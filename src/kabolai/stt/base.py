"""Abstract base class for Speech-to-Text engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class TranscriptionResult:
    """Result from STT transcription."""
    text: str
    language: Optional[str] = None
    confidence: float = 0.0
    is_final: bool = True


class STTEngine(ABC):
    """Abstract Speech-to-Text engine."""

    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Load the STT model from disk."""
        ...

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio data to text."""
        ...

    @abstractmethod
    def supports_language(self, lang_code: str) -> bool:
        """Check if this engine supports the given language."""
        ...

    def cleanup(self) -> None:
        """Release model resources."""
        pass
