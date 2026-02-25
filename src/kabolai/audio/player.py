"""Audio playback via sounddevice."""

import io
import logging

import numpy as np
import sounddevice as sd
import soundfile as sf

from kabolai.core.exceptions import AudioError

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Plays audio data through speakers."""

    def __init__(self, config=None):
        self._config = config

    def play_bytes(self, audio_bytes: bytes, sample_rate: int = 22050, channels: int = 1):
        """Play raw PCM int16 audio bytes."""
        try:
            audio = np.frombuffer(audio_bytes, dtype=np.int16)
            if channels > 1:
                audio = audio.reshape(-1, channels)
            audio_float = audio.astype(np.float32) / 32768.0
            sd.play(audio_float, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            raise AudioError(f"Playback error: {e}") from e

    def play_wav(self, wav_bytes: bytes):
        """Play WAV-formatted audio bytes."""
        try:
            with io.BytesIO(wav_bytes) as buf:
                data, sample_rate = sf.read(buf)
            sd.play(data, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            raise AudioError(f"WAV playback error: {e}") from e

    def play_file(self, filepath: str):
        """Play an audio file."""
        try:
            data, sample_rate = sf.read(filepath)
            sd.play(data, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            raise AudioError(f"File playback error: {e}") from e

    def stop(self):
        """Stop current playback."""
        sd.stop()

    def cleanup(self):
        """Release resources."""
        self.stop()
