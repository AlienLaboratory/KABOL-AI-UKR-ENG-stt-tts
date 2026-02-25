"""Factory for creating TTS engines based on config."""

import logging

from kabolai.core.config import AppConfig
from kabolai.tts.base import TTSEngine

logger = logging.getLogger(__name__)


def create_tts_engine(config: AppConfig, lang: str = "en") -> TTSEngine:
    """Create the appropriate TTS engine for the given language."""
    tts_config = config.tts

    if lang == "uk":
        uk_cfg = tts_config.get("ukrainian", {})
        from kabolai.tts.ukrainian_engine import UkrainianTTS

        return UkrainianTTS(
            voice=uk_cfg.get("voice", "Dmytro"),
            stress=uk_cfg.get("stress", "Dictionary"),
            device=uk_cfg.get("device", "cpu"),
        )

    # English
    en_cfg = tts_config.get("english", {})
    engine_type = en_cfg.get("engine", "pyttsx3")

    if engine_type == "piper":
        try:
            from kabolai.tts.piper_engine import PiperTTS

            piper_cfg = en_cfg.get("piper", {})
            return PiperTTS(
                model=piper_cfg.get("model", "en_US-lessac-medium"),
                model_path=piper_cfg.get("model_path"),
            )
        except Exception as e:
            logger.warning(f"Piper TTS failed, falling back to pyttsx3: {e}")

    # Default: pyttsx3
    from kabolai.tts.pyttsx3_engine import Pyttsx3TTS

    pyttsx3_cfg = en_cfg.get("pyttsx3", {})
    return Pyttsx3TTS(
        rate=pyttsx3_cfg.get("rate", 175),
        volume=pyttsx3_cfg.get("volume", 0.9),
    )
