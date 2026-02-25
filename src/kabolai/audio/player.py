"""Audio playback via sounddevice with timeout protection."""

import io
import logging
import time

import numpy as np
import sounddevice as sd
import soundfile as sf

from kabolai.core.exceptions import AudioError

logger = logging.getLogger(__name__)

# Maximum seconds any single playback can last
PLAYBACK_TIMEOUT = 30


class AudioPlayer:
    """Plays audio data through speakers with timeout protection."""

    def __init__(self, config=None):
        self._config = config

    def _wait_with_timeout(self, timeout: float = PLAYBACK_TIMEOUT):
        """Wait for playback to finish with a timeout guard.

        Prevents sd.wait() from hanging forever if the audio device
        has issues. Forces stop after timeout seconds.
        """
        start = time.monotonic()
        while True:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                logger.warning(
                    f"Playback timed out after {timeout:.0f}s — force stopping."
                )
                sd.stop()
                return
            # Check if playback is still active
            try:
                stream = sd.get_stream()
                if stream is None or not stream.active:
                    return
            except Exception:
                return
            time.sleep(0.05)

    def play_bytes(self, audio_bytes: bytes, sample_rate: int = 22050, channels: int = 1):
        """Play raw PCM int16 audio bytes."""
        try:
            audio = np.frombuffer(audio_bytes, dtype=np.int16)
            if channels > 1:
                audio = audio.reshape(-1, channels)
            audio_float = audio.astype(np.float32) / 32768.0
            sd.play(audio_float, samplerate=sample_rate)
            self._wait_with_timeout()
        except AudioError:
            raise
        except Exception as e:
            raise AudioError(f"Playback error: {e}") from e

    def play_wav(self, wav_bytes: bytes):
        """Play WAV-formatted audio bytes."""
        try:
            with io.BytesIO(wav_bytes) as buf:
                data, sample_rate = sf.read(buf)
            sd.play(data, samplerate=sample_rate)
            self._wait_with_timeout()
        except AudioError:
            raise
        except Exception as e:
            raise AudioError(f"WAV playback error: {e}") from e

    def play_file(self, filepath: str):
        """Play an audio file."""
        try:
            data, sample_rate = sf.read(filepath)
            sd.play(data, samplerate=sample_rate)
            self._wait_with_timeout()
        except AudioError:
            raise
        except Exception as e:
            raise AudioError(f"File playback error: {e}") from e

    def stop(self):
        """Stop current playback."""
        try:
            sd.stop()
        except Exception:
            pass

    def cleanup(self):
        """Release resources."""
        self.stop()
