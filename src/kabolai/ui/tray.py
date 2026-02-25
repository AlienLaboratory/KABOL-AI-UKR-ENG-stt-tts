"""System tray icon with pystray."""

import logging
import threading
from typing import Callable, Optional

import pystray

from kabolai.core.state import AssistantState
from kabolai.ui.icons import create_icon

logger = logging.getLogger(__name__)


class SystemTray:
    """System tray icon for KA-BOL-AI."""

    def __init__(
        self,
        state: AssistantState,
        on_toggle: Optional[Callable] = None,
        on_language: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        self.state = state
        self._on_toggle = on_toggle
        self._on_language = on_language
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None

    def _build_menu(self) -> pystray.Menu:
        status_text = "Active" if self.state.is_active else "Inactive"
        lang_text = "UK" if self.state.language == "uk" else "EN"

        return pystray.Menu(
            pystray.MenuItem(
                f"KA-BOL-AI [{status_text}] [{lang_text}]",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Toggle On/Off (Ctrl+Shift+A)",
                self._handle_toggle,
            ),
            pystray.MenuItem(
                "Switch Language (Ctrl+Shift+L)",
                self._handle_language,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit (Ctrl+Shift+Q)",
                self._handle_quit,
            ),
        )

    def _handle_toggle(self, icon, item):
        if self._on_toggle:
            self._on_toggle()
        self.update_icon()

    def _handle_language(self, icon, item):
        if self._on_language:
            self._on_language()
        self.update_icon()

    def _handle_quit(self, icon, item):
        if self._on_quit:
            self._on_quit()
        if self._icon:
            self._icon.stop()

    def update_icon(self):
        """Update the tray icon based on current state."""
        if self._icon:
            self._icon.icon = create_icon(active=self.state.is_active)
            self._icon.menu = self._build_menu()

    def run(self):
        """Run the system tray icon (blocking — run in a thread)."""
        self._icon = pystray.Icon(
            name="kabolai",
            icon=create_icon(active=self.state.is_active),
            title="KA-BOL-AI Voice Assistant",
            menu=self._build_menu(),
        )
        logger.info("System tray icon started.")
        self._icon.run()

    def run_in_background(self):
        """Start the tray icon in a background thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            self._icon.stop()
