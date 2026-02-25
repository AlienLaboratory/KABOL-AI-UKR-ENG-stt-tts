"""Microphone audio capture with silence detection."""

import logging
import queue
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

from kabolai.core.config import AudioConfig
from kabolai.core.exceptions import AudioError

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Records audio from microphone with voice activity detection."""

    def __init__(self, config: AudioConfig):
        self.sample_rate = config.sample_rate
        self.channels = config.channels
        self.chunk_size = config.chunk_size
        self.silence_threshold = config.silence_threshold
        self.silence_duration = config.silence_duration
        self.max_record_seconds = config.max_record_seconds

        self._audio_queue: queue.Queue = queue.Queue()
        self._is_recording = False
        self._record_event = threading.Event()

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice InputStream."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self._audio_queue.put(indata.copy())

    def record(self) -> Optional[np.ndarray]:
        """Record audio until silence is detected or max duration reached.

        Returns:
            numpy array of int16 audio samples, or None if no speech detected.
        """
        self._is_recording = True
        self._audio_queue = queue.Queue()
        chunks = []
        silence_chunks = 0
        chunks_per_second = self.sample_rate / self.chunk_size
        silence_chunks_threshold = int(self.silence_duration * chunks_per_second)
        max_chunks = int(self.max_record_seconds * chunks_per_second)
        has_speech = False

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=self._audio_callback,
            ):
                logger.info("Recording... (speak now)")
                chunk_count = 0

                while self._is_recording and chunk_count < max_chunks:
                    try:
                        chunk = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    chunks.append(chunk)
                    chunk_count += 1

                    # Check RMS for silence detection
                    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                    if rms < self.silence_threshold:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0
                        has_speech = True

                    # Stop if enough silence after speech
                    if has_speech and silence_chunks >= silence_chunks_threshold:
                        logger.info("Silence detected, stopping recording.")
                        break

        except sd.PortAudioError as e:
            raise AudioError(f"Microphone error: {e}") from e
        finally:
            self._is_recording = False

        if not chunks or not has_speech:
            logger.info("No speech detected.")
            return None

        audio = np.concatenate(chunks, axis=0).flatten()
        logger.info(f"Recorded {len(audio) / self.sample_rate:.1f}s of audio.")
        return audio

    def stop(self):
        """Stop recording early."""
        self._is_recording = False

    def list_devices(self) -> list[dict]:
        """List available audio input devices."""
        devices = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    def cleanup(self):
        """Release resources."""
        self.stop()
