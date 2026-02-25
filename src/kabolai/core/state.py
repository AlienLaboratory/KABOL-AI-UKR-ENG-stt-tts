"""Thread-safe assistant state with self-healing watchdog."""

import logging
import threading
import time

logger = logging.getLogger(__name__)

# Maximum seconds any single pipeline run can take before auto-reset
PIPELINE_TIMEOUT = 60


class AssistantState:
    """Mutable state shared across threads with automatic hang recovery."""

    def __init__(self, language: str = "en"):
        self.language = language
        self.is_active = True
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        self.is_running = True
        self._lock = threading.Lock()
        # Timestamp when pipeline started (for watchdog)
        self._pipeline_start: float = 0.0
        # Voice pipeline lock — prevents overlapping voice commands
        self._voice_lock = threading.Lock()

    @property
    def is_busy(self) -> bool:
        """True if any part of the voice pipeline is active."""
        return self.is_listening or self.is_processing or self.is_speaking

    def try_start_pipeline(self) -> bool:
        """Attempt to start the voice pipeline. Returns False if already busy.

        This uses a non-blocking lock to prevent overlapping voice commands.
        Also includes self-healing: if the pipeline has been running for too
        long, forcefully reset it and allow the new command through.
        """
        # Self-healing: check if previous pipeline is stuck
        if self._pipeline_start > 0:
            elapsed = time.monotonic() - self._pipeline_start
            if elapsed > PIPELINE_TIMEOUT:
                logger.warning(
                    f"Pipeline stuck for {elapsed:.0f}s — "
                    f"auto-resetting (self-healing)"
                )
                self.force_reset()
                # Release the voice lock if it's held
                if self._voice_lock.locked():
                    try:
                        self._voice_lock.release()
                    except RuntimeError:
                        pass

        acquired = self._voice_lock.acquire(blocking=False)
        if acquired:
            with self._lock:
                self._pipeline_start = time.monotonic()
            return True
        return False

    def end_pipeline(self):
        """Mark the voice pipeline as complete and release the lock."""
        with self._lock:
            self.is_listening = False
            self.is_processing = False
            self.is_speaking = False
            self._pipeline_start = 0.0
        try:
            self._voice_lock.release()
        except RuntimeError:
            pass

    def force_reset(self):
        """Force-reset all busy states. Used by watchdog / self-healing."""
        with self._lock:
            self.is_listening = False
            self.is_processing = False
            self.is_speaking = False
            self._pipeline_start = 0.0
        logger.info("State force-reset: all flags cleared.")

    def toggle_language(self) -> str:
        with self._lock:
            self.language = "uk" if self.language == "en" else "en"
            return self.language

    def set_language(self, lang: str) -> str:
        with self._lock:
            if lang in ("en", "uk"):
                self.language = lang
            return self.language

    def toggle_active(self) -> bool:
        with self._lock:
            self.is_active = not self.is_active
            return self.is_active

    def set_listening(self, value: bool):
        with self._lock:
            self.is_listening = value

    def set_processing(self, value: bool):
        with self._lock:
            self.is_processing = value

    def set_speaking(self, value: bool):
        with self._lock:
            self.is_speaking = value

    def shutdown(self):
        with self._lock:
            self.is_running = False
            self.is_active = False
            self.is_listening = False
            self.is_processing = False
            self.is_speaking = False
            self._pipeline_start = 0.0
