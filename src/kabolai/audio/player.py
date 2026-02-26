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
    """Plays audio data through speakers with timeout and cancel support.

    The _stopped event can be set externally (by assistant.interrupt())
    to immediately halt playback mid-sentence.
    """

    def __init__(self, config=None):
        self._config = config
        self._stopped = False

    def _wait_with_timeout(self, timeout: float = PLAYBACK_TIMEOUT):
        """Wait for playback with timeout and cancel support.

        Checks self._stopped every 50ms — when set, halts immediately.
        This enables instant interrupt when the user speaks.
        """
        start = time.monotonic()
        while True:
            # Check cancel/stop flag
            if self._stopped:
                sd.stop()
                return

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
        """Stop current playback immediately."""
        self._stopped = True
        try:
            sd.stop()
        except Exception:
            pass
        # Reset flag after stopping
        self._stopped = False

    def cleanup(self):
        """Release resources."""
        self.stop()
