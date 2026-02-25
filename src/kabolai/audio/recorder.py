"""Microphone audio capture with auto-calibration and continuous listening.

Key features:
- Auto-calibrate: measures ambient noise on first use, sets threshold dynamically
- Pre-buffer: keeps ~0.5s of audio BEFORE speech starts (prevents cutting words)
- Interrupt-friendly: continuous mode detects speech even while pipeline is busy
"""

import collections
import logging
import queue
import threading
import time
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from kabolai.core.config import AudioConfig
from kabolai.core.exceptions import AudioError

logger = logging.getLogger(__name__)

# Minimum speech duration (seconds) before we consider it real speech
MIN_SPEECH_DURATION = 0.3

# Pre-buffer: keep this many seconds of audio before speech starts
PRE_BUFFER_DURATION = 0.5

# Cooldown after processing (seconds) to avoid hearing the TTS response
POST_SPEECH_COOLDOWN = 1.0

# Auto-calibration settings
CALIBRATION_DURATION = 1.0  # seconds of ambient noise to record
SPEECH_MULTIPLIER = 3.0     # speech threshold = ambient * this
MIN_SPEECH_THRESHOLD = 100  # absolute minimum speech threshold


class AudioRecorder:
    """Records audio from microphone with auto-calibrated voice detection.

    On first use, records 1 second of ambient noise to calibrate the speech
    detection threshold. This ensures continuous mode works regardless of
    microphone sensitivity or background noise level.
    """

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

        # Continuous listening state
        self._continuous = False
        self._continuous_thread: Optional[threading.Thread] = None
        self._on_speech_callback: Optional[Callable] = None
        self._cooldown_until: float = 0.0

        # Auto-calibration
        self._calibrated = False
        self._ambient_rms: float = 0.0
        self._speech_threshold: float = float(config.silence_threshold)

        # Log audio device info
        self._log_device_info()

    def _log_device_info(self):
        """Log which audio input device is being used."""
        try:
            default_idx = sd.default.device[0]
            device = sd.query_devices(default_idx)
            logger.info(
                f"Audio input: [{default_idx}] {device['name']} "
                f"(native {device['default_samplerate']:.0f}Hz, "
                f"{device['max_input_channels']}ch, "
                f"requesting {self.sample_rate}Hz {self.channels}ch)"
            )
        except Exception as e:
            logger.warning(f"Could not query audio device: {e}")

    def calibrate(self):
        """Record ambient noise and auto-set speech detection threshold.

        Should be called once during initialization. Measures the ambient
        noise level and sets the threshold to SPEECH_MULTIPLIER times that.
        """
        logger.info(f"Calibrating microphone ({CALIBRATION_DURATION}s)...")
        try:
            audio = sd.rec(
                int(self.sample_rate * CALIBRATION_DURATION),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()
            audio = audio.flatten()

            self._ambient_rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
            self._speech_threshold = max(
                MIN_SPEECH_THRESHOLD,
                self._ambient_rms * SPEECH_MULTIPLIER,
            )
            self._calibrated = True

            # Also update silence_threshold if our calibration gives a better value
            # (use a lower multiplier for silence detection — 2x ambient)
            calibrated_silence = max(80, self._ambient_rms * 2)
            if self.silence_threshold > self._speech_threshold:
                # Config threshold is too high, override with calibrated
                old = self.silence_threshold
                self.silence_threshold = self._speech_threshold
                logger.info(
                    f"Overriding silence_threshold: {old:.0f} → "
                    f"{self.silence_threshold:.0f} (was higher than speech threshold)"
                )

            logger.info(
                f"Calibration complete: ambient_rms={self._ambient_rms:.0f}, "
                f"speech_threshold={self._speech_threshold:.0f}, "
                f"silence_threshold={self.silence_threshold:.0f}"
            )
        except Exception as e:
            logger.warning(f"Calibration failed: {e}. Using config threshold.")
            self._speech_threshold = float(self.silence_threshold)

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice InputStream."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self._audio_queue.put(indata.copy())

    # ---- Push-to-talk mode ----

    def record(self) -> Optional[np.ndarray]:
        """Record audio until silence is detected or max duration reached."""
        # Auto-calibrate on first use
        if not self._calibrated:
            self.calibrate()

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

                    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                    if rms < self.silence_threshold:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0
                        has_speech = True

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
        duration = len(audio) / self.sample_rate
        audio_rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
        logger.info(
            f"Recorded {duration:.1f}s of audio "
            f"(RMS={audio_rms:.0f}, peak={np.max(np.abs(audio)):.0f})"
        )
        return audio

    # ---- Continuous listening mode ----

    def start_continuous(self, on_speech: Callable[[np.ndarray], None]):
        """Start continuous listening mode."""
        if self._continuous:
            logger.warning("Continuous listening already active.")
            return

        # Auto-calibrate on first use
        if not self._calibrated:
            self.calibrate()

        self._on_speech_callback = on_speech
        self._continuous = True
        self._continuous_thread = threading.Thread(
            target=self._continuous_loop, daemon=True, name="continuous-listener"
        )
        self._continuous_thread.start()
        logger.info(
            f"Continuous listening started "
            f"(speech_threshold={self._speech_threshold:.0f})"
        )

    def stop_continuous(self):
        """Stop continuous listening mode."""
        self._continuous = False
        if self._continuous_thread and self._continuous_thread.is_alive():
            self._continuous_thread.join(timeout=3)
        self._continuous_thread = None
        logger.info("Continuous listening stopped.")

    def set_cooldown(self, seconds: float = POST_SPEECH_COOLDOWN):
        """Set a cooldown period to prevent hearing own TTS output."""
        self._cooldown_until = time.monotonic() + seconds

    def _continuous_loop(self):
        """Background loop: always-on microphone → detect speech → callback."""
        audio_q = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Continuous audio status: {status}")
            audio_q.put(indata.copy())

        chunks_per_second = self.sample_rate / self.chunk_size
        silence_threshold_chunks = int(self.silence_duration * chunks_per_second)
        min_speech_chunks = int(MIN_SPEECH_DURATION * chunks_per_second)
        max_chunks = int(self.max_record_seconds * chunks_per_second)
        pre_buffer_size = max(1, int(PRE_BUFFER_DURATION * chunks_per_second))

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=callback,
            ):
                logger.info("Continuous listener: microphone open, waiting for speech...")
                while self._continuous:
                    self._wait_for_speech(
                        audio_q, chunks_per_second,
                        silence_threshold_chunks, min_speech_chunks,
                        max_chunks, pre_buffer_size,
                    )

        except sd.PortAudioError as e:
            logger.error(f"Continuous listener mic error: {e}")
        except Exception as e:
            logger.error(f"Continuous listener error: {e}", exc_info=True)
        finally:
            logger.info("Continuous listener exited.")

    def _wait_for_speech(self, audio_q, chunks_per_second,
                         silence_threshold_chunks, min_speech_chunks,
                         max_chunks, pre_buffer_size):
        """Wait for speech, record it (with pre-buffer), then trigger callback."""
        chunks = []
        silence_count = 0
        speech_count = 0
        recording = False

        # Use calibrated speech threshold for continuous detection
        speech_threshold = self._speech_threshold

        # Pre-buffer: keep the last N chunks of audio before speech starts
        pre_buffer = collections.deque(maxlen=pre_buffer_size)

        while self._continuous:
            try:
                chunk = audio_q.get(timeout=0.5)
            except queue.Empty:
                continue

            # Check cooldown (ignore audio right after TTS playback)
            if time.monotonic() < self._cooldown_until:
                pre_buffer.clear()
                continue

            rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

            if not recording:
                # Waiting for speech to start — keep pre-buffer rolling
                pre_buffer.append(chunk)

                if rms >= speech_threshold:
                    recording = True
                    # Include pre-buffer audio so word beginnings aren't cut off
                    chunks = list(pre_buffer)
                    speech_count = 1
                    silence_count = 0
                    logger.debug(
                        f"Speech detected (RMS={rms:.0f} >= {speech_threshold:.0f}), "
                        f"pre-buffer: {len(chunks)} chunks"
                    )
            else:
                # Currently recording speech
                chunks.append(chunk)

                if rms >= speech_threshold:
                    silence_count = 0
                    speech_count += 1
                else:
                    silence_count += 1

                # Stop conditions
                if silence_count >= silence_threshold_chunks:
                    if speech_count >= min_speech_chunks:
                        audio = np.concatenate(chunks, axis=0).flatten()
                        duration = len(audio) / self.sample_rate
                        audio_rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
                        logger.info(
                            f"Speech ended ({duration:.1f}s, {speech_count} chunks, "
                            f"RMS={audio_rms:.0f})"
                        )
                        if self._on_speech_callback:
                            try:
                                self._on_speech_callback(audio)
                            except Exception as e:
                                logger.error(f"Speech callback error: {e}")
                    else:
                        logger.debug(
                            f"Too short ({speech_count} chunks), ignoring"
                        )
                    return

                if len(chunks) >= max_chunks:
                    audio = np.concatenate(chunks, axis=0).flatten()
                    logger.info(
                        f"Max recording duration reached ({self.max_record_seconds}s)"
                    )
                    if self._on_speech_callback and speech_count >= min_speech_chunks:
                        try:
                            self._on_speech_callback(audio)
                        except Exception as e:
                            logger.error(f"Speech callback error: {e}")
                    return

    def stop(self):
        """Stop recording early."""
        self._is_recording = False
        self._continuous = False

    def list_devices(self) -> list:
        """List available audio input devices."""
        devices = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    def cleanup(self):
        """Release resources."""
        self.stop_continuous()
        self.stop()
