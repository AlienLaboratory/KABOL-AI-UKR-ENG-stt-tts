"""Constants for KA-BOL-AI."""

import sys
from pathlib import Path

# Project root — handles both normal and PyInstaller frozen mode
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle: exe is in dist/KA-BOL-AI/
    PROJECT_ROOT = Path(sys.executable).parent
else:
    # Normal Python: core/ -> kabolai/ -> src/ -> project root
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Default paths
CONFIG_DIR = PROJECT_ROOT / "config"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Supported languages
SUPPORTED_LANGUAGES = ("en", "uk")
DEFAULT_LANGUAGE = "en"

# VOSK model download info (flat lookup by key)
VOSK_MODELS = {
    "en_small": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "dir_name": "vosk-model-small-en-us-0.15",
        "size_mb": 40,
    },
    "en_large": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip",
        "dir_name": "vosk-model-en-us-0.22-lgraph",
        "size_mb": 128,
    },
    "uk_small": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-uk-v3-nano.zip",
        "dir_name": "vosk-model-small-uk-v3-nano",
        "size_mb": 73,
    },
    "uk_large": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-uk-v3-small.zip",
        "dir_name": "vosk-model-uk-v3-small",
        "size_mb": 133,
    },
}

# VOSK model URLs mapped by profile -> language
# This is what the GUI wizard uses to know what to download
VOSK_MODEL_URLS = {
    "cpu": {
        "en": VOSK_MODELS["en_small"],
        "uk": VOSK_MODELS["uk_small"],
    },
    "gpu_light": {
        "en": VOSK_MODELS["en_large"],
        "uk": VOSK_MODELS["uk_large"],
    },
    "gpu_full": {
        "en": VOSK_MODELS["en_large"],
        "uk": VOSK_MODELS["uk_large"],
    },
}

# Hardware profile to model mapping
PROFILE_MODELS = {
    "cpu": {
        "vosk_en": "en_small",
        "vosk_uk": "uk_small",
        "ollama": "qwen2.5:1.5b",
        "tts_en": "pyttsx3",
    },
    "gpu_light": {
        "vosk_en": "en_large",
        "vosk_uk": "uk_large",
        "ollama": "mistral:7b-q4_0",
        "tts_en": "piper",
    },
    "gpu_full": {
        "vosk_en": "en_large",
        "vosk_uk": "uk_large",
        "ollama": "llama3:8b",
        "tts_en": "piper",
        "stt_engine": "whisper",
    },
}

# Audio defaults
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
