"""Thread-safe assistant state."""

import threading


class AssistantState:
    """Mutable state shared across threads."""

    def __init__(self, language: str = "en"):
        self.language = language
        self.is_active = True
        self.is_listening = False
        self.is_processing = False
        self.is_running = True
        self._lock = threading.Lock()

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

    def shutdown(self):
        with self._lock:
            self.is_running = False
            self.is_active = False
