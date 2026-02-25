"""Abstract base class for Text-to-Speech engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SpeechResult:
    """Result from TTS synthesis."""
    audio_data: bytes  # WAV-formatted audio bytes
    sample_rate: int = 22050
    format: str = "wav"  # "wav" or "raw"


class TTSEngine(ABC):
    """Abstract Text-to-Speech engine."""

    @abstractmethod
    def synthesize(self, text: str) -> SpeechResult:
        """Convert text to speech audio."""
        ...

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """List available voice identifiers."""
        ...

    def set_voice(self, voice_id: str) -> None:
        """Set the active voice. Override if supported."""
        pass

    def set_speed(self, speed: float) -> None:
        """Set speech rate (1.0 = normal). Override if supported."""
        pass

    def cleanup(self) -> None:
        """Release engine resources."""
        pass
