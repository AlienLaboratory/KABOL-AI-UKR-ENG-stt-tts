"""Exception hierarchy for KA-BOL-AI."""


class KabolaiError(Exception):
    """Base exception for all KA-BOL-AI errors."""


class ConfigError(KabolaiError):
    """Configuration loading or validation error."""


class AudioError(KabolaiError):
    """Audio recording or playback error."""


class STTError(KabolaiError):
    """Speech-to-text engine error."""


class TTSError(KabolaiError):
    """Text-to-speech engine error."""


class BrainError(KabolaiError):
    """LLM brain processing error."""


class ActionError(KabolaiError):
    """Action execution error."""


class ModelNotFoundError(KabolaiError):
    """Required model file not found."""
