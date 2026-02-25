"""Factory for creating STT engines based on config."""

import logging
from pathlib import Path

from kabolai.core.config import AppConfig
from kabolai.core.constants import MODELS_DIR
from kabolai.stt.base import STTEngine

logger = logging.getLogger(__name__)


def create_stt_engine(config: AppConfig) -> STTEngine:
    """Create and initialize the appropriate STT engine."""
    stt_config = config.stt
    engine_type = stt_config.get("engine", "vosk")

    if engine_type == "whisper":
        from kabolai.stt.whisper_engine import WhisperSTT

        whisper_cfg = stt_config.get("whisper", {})
        engine = WhisperSTT(
            model_size=whisper_cfg.get("model_size", "base"),
            device=whisper_cfg.get("device", "cuda"),
            compute_type=whisper_cfg.get("compute_type", "float16"),
        )
        engine.load_model()
        return engine

    # Default: VOSK
    from kabolai.stt.vosk_engine import VoskSTT

    engine = VoskSTT()
    vosk_cfg = stt_config.get("vosk", {})

    # Load English model
    en_path = vosk_cfg.get("model_en", str(MODELS_DIR / "vosk" / "en"))
    en_path = Path(en_path)
    if en_path.exists():
        engine.load_model(str(en_path), language="en")
    else:
        logger.warning(f"English VOSK model not found at {en_path}")

    # Load Ukrainian model
    uk_path = vosk_cfg.get("model_uk", str(MODELS_DIR / "vosk" / "uk"))
    uk_path = Path(uk_path)
    if uk_path.exists():
        engine.load_model(str(uk_path), language="uk")
    else:
        logger.warning(f"Ukrainian VOSK model not found at {uk_path}")

    return engine
