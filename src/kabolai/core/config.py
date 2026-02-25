"""Configuration system with YAML loading and profile merging."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from kabolai.core.constants import CONFIG_DIR
from kabolai.core.exceptions import ConfigError


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 4000
    silence_threshold: int = 500
    silence_duration: float = 1.5
    max_record_seconds: int = 30


@dataclass
class HotkeyConfig:
    push_to_talk: str = "ctrl+q"
    toggle_active: str = "ctrl+shift+a"
    toggle_language: str = "ctrl+shift+l"
    quit: str = "ctrl+shift+x"


@dataclass
class AppConfig:
    profile: str = "cpu"
    language: str = "en"
    audio: AudioConfig = field(default_factory=AudioConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    stt: dict = field(default_factory=dict)
    tts: dict = field(default_factory=dict)
    brain: dict = field(default_factory=dict)
    logging: dict = field(default_factory=dict)

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> "AppConfig":
        """Load config from YAML, apply profile overlay."""
        default_path = CONFIG_DIR / "default.yaml"
        if not default_path.exists():
            raise ConfigError(f"Default config not found: {default_path}")

        with open(default_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Apply profile overlay
        profile_name = profile or config_data.get("profile", "cpu")
        profile_path = CONFIG_DIR / "profiles" / f"{profile_name}.yaml"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = yaml.safe_load(f) or {}
            config_data = deep_merge(config_data, profile_data)

        # Apply user override
        if config_path:
            user_path = Path(config_path)
            if not user_path.exists():
                raise ConfigError(f"User config not found: {user_path}")
            with open(user_path, "r", encoding="utf-8") as f:
                user_data = yaml.safe_load(f) or {}
            config_data = deep_merge(config_data, user_data)

        return cls._from_dict(config_data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        audio_data = data.get("audio", {})
        hotkey_data = data.get("hotkeys", {})

        return cls(
            profile=data.get("profile", "cpu"),
            language=data.get("language", "en"),
            audio=AudioConfig(**{
                k: v for k, v in audio_data.items()
                if k in AudioConfig.__dataclass_fields__
            }),
            hotkeys=HotkeyConfig(**{
                k: v for k, v in hotkey_data.items()
                if k in HotkeyConfig.__dataclass_fields__
            }),
            stt=data.get("stt", {}),
            tts=data.get("tts", {}),
            brain=data.get("brain", {}),
            logging=data.get("logging", {}),
        )
