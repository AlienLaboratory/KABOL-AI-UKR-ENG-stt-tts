"""Factory for creating brain engines based on config."""

import logging

from kabolai.core.config import AppConfig
from kabolai.brain.base import BrainEngine

logger = logging.getLogger(__name__)


def create_brain(config: AppConfig) -> BrainEngine:
    """Create the appropriate brain engine."""
    brain_config = config.brain
    engine_type = brain_config.get("engine", "ollama")

    if engine_type == "ollama":
        from kabolai.brain.ollama_brain import OllamaBrain

        ollama_cfg = brain_config.get("ollama", {})
        return OllamaBrain(
            base_url=ollama_cfg.get("base_url", "http://localhost:11434"),
            model=ollama_cfg.get("model", "qwen2.5:1.5b"),
            temperature=ollama_cfg.get("temperature", 0.1),
            timeout=ollama_cfg.get("timeout", 30),
        )

    raise ValueError(f"Unknown brain engine: {engine_type}")
