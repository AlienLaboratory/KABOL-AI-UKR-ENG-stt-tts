"""Global hotkey listener using keyboard library."""

import logging
import threading
from typing import Callable, Optional

import keyboard

from kabolai.core.config import HotkeyConfig

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Manages global hotkey bindings."""

    def __init__(self, config: HotkeyConfig):
        self.config = config
        self._hooks = []

    def bind(
        self,
        on_push_to_talk: Callable,
        on_toggle_active: Callable,
        on_toggle_language: Callable,
        on_quit: Callable,
    ):
        """Bind all hotkeys."""
        try:
            keyboard.add_hotkey(
                self.config.push_to_talk, on_push_to_talk,
                suppress=False, trigger_on_release=False,
            )
            logger.info(f"Bound push-to-talk: {self.config.push_to_talk}")

            keyboard.add_hotkey(
                self.config.toggle_active, on_toggle_active,
                suppress=False,
            )
            logger.info(f"Bound toggle-active: {self.config.toggle_active}")

            keyboard.add_hotkey(
                self.config.toggle_language, on_toggle_language,
                suppress=False,
            )
            logger.info(f"Bound toggle-language: {self.config.toggle_language}")

            keyboard.add_hotkey(
                self.config.quit, on_quit,
                suppress=False,
            )
            logger.info(f"Bound quit: {self.config.quit}")

        except Exception as e:
            logger.error(f"Failed to bind hotkeys: {e}")
            raise

    def unbind_all(self):
        """Remove all hotkey bindings."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    def wait(self):
        """Block until quit hotkey is pressed."""
        keyboard.wait()
