"""Shared test fixtures for KA-BOL-AI."""

import pytest
import numpy as np

from kabolai.core.config import AppConfig, AudioConfig, HotkeyConfig
from kabolai.core.state import AssistantState


@pytest.fixture
def mock_config():
    """Minimal config for testing."""
    return AppConfig(
        profile="cpu",
        language="en",
        audio=AudioConfig(sample_rate=16000, channels=1),
        hotkeys=HotkeyConfig(),
        stt={
            "engine": "vosk",
            "vosk": {"model_en": "test_model", "model_uk": "test_model"},
        },
        tts={
            "english": {"engine": "pyttsx3"},
            "ukrainian": {"engine": "ukrainian_tts", "voice": "Dmytro"},
        },
        brain={
            "engine": "ollama",
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:1.5b",
                "temperature": 0.1,
                "timeout": 10,
            },
        },
    )


@pytest.fixture
def sample_audio():
    """Generate 2 seconds of silence as test audio."""
    return np.zeros(32000, dtype=np.int16)


@pytest.fixture
def sample_speech_audio():
    """Generate 2 seconds of fake speech (sine wave) as test audio."""
    t = np.linspace(0, 2, 32000, dtype=np.float32)
    signal = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)
    return signal


@pytest.fixture
def assistant_state():
    """Fresh assistant state."""
    return AssistantState(language="en")
