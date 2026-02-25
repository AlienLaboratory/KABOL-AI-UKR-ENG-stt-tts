"""Tests for configuration system."""

import pytest
from pathlib import Path

from kabolai.core.config import AppConfig, AudioConfig, HotkeyConfig, deep_merge


class TestDeepMerge:
    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 99, "z": 100}}
        result = deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 99, "z": 100}, "b": 3}

    def test_override_replaces_non_dict(self):
        base = {"a": 1}
        override = {"a": {"nested": True}}
        result = deep_merge(base, override)
        assert result == {"a": {"nested": True}}

    def test_empty_override(self):
        base = {"a": 1}
        result = deep_merge(base, {})
        assert result == {"a": 1}


class TestAudioConfig:
    def test_defaults(self):
        cfg = AudioConfig()
        assert cfg.sample_rate == 16000
        assert cfg.channels == 1
        assert cfg.silence_duration == 0.8
        assert cfg.max_record_seconds == 30


class TestHotkeyConfig:
    def test_defaults(self):
        cfg = HotkeyConfig()
        assert cfg.push_to_talk == "ctrl+q"
        assert cfg.toggle_language == "ctrl+shift+l"
        assert cfg.quit == "ctrl+shift+x"


class TestAppConfig:
    def test_default_values(self):
        cfg = AppConfig()
        assert cfg.profile == "cpu"
        assert cfg.language == "en"

    def test_from_dict(self):
        data = {
            "profile": "gpu_light",
            "language": "uk",
            "audio": {"sample_rate": 22050},
            "hotkeys": {"quit": "ctrl+q"},
            "stt": {"engine": "whisper"},
        }
        cfg = AppConfig._from_dict(data)
        assert cfg.profile == "gpu_light"
        assert cfg.language == "uk"
        assert cfg.audio.sample_rate == 22050
        assert cfg.hotkeys.quit == "ctrl+q"
        assert cfg.stt["engine"] == "whisper"
