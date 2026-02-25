"""Ukrainian TTS using robinhad/ukrainian-tts (ESPnet v2)."""

import io
import logging

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)


class UkrainianTTS(TTSEngine):
    """Ukrainian TTS using the ukrainian-tts package."""

    def __init__(self, voice: str = "Dmytro", stress: str = "Dictionary", device: str = "cpu"):
        self._voice_name = voice
        self._stress_name = stress
        self._device = device
        self._tts = None
        self._voices_enum = None
        self._stress_enum = None
        self._initialize()

    def _initialize(self):
        """Lazy-initialize the TTS engine."""
        try:
            from ukrainian_tts.tts import TTS, Voices, Stress

            self._voices_enum = Voices
            self._stress_enum = Stress
            self._tts = TTS(device=self._device)
            logger.info(
                f"Ukrainian TTS initialized: voice={self._voice_name}, "
                f"stress={self._stress_name}, device={self._device}"
            )
        except ImportError:
            raise TTSError(
                "ukrainian-tts not installed. Run: "
                "pip install git+https://github.com/robinhad/ukrainian-tts.git"
            )
        except Exception as e:
            raise TTSError(f"Failed to initialize Ukrainian TTS: {e}") from e

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize Ukrainian text to WAV audio."""
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        try:
            voice_val = getattr(self._voices_enum, self._voice_name).value
            stress_val = getattr(self._stress_enum, self._stress_name).value

            wav_buffer = io.BytesIO()
            _, output_text = self._tts.tts(text, voice_val, stress_val, wav_buffer)
            wav_data = wav_buffer.getvalue()

            logger.debug(f"Ukrainian TTS: '{text[:50]}...' -> {len(wav_data)} bytes")

            return SpeechResult(audio_data=wav_data, sample_rate=22050, format="wav")
        except Exception as e:
            raise TTSError(f"Ukrainian TTS synthesis failed: {e}") from e

    def get_available_voices(self) -> list[str]:
        if self._voices_enum:
            return [v.name for v in self._voices_enum]
        return ["Oleksa", "Tetiana", "Dmytro", "Lada", "Mykyta"]

    def set_voice(self, voice_id: str) -> None:
        if self._voices_enum and hasattr(self._voices_enum, voice_id):
            self._voice_name = voice_id
        else:
            logger.warning(f"Unknown Ukrainian voice: {voice_id}")

    def cleanup(self) -> None:
        self._tts = None
