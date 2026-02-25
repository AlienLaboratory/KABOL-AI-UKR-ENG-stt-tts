"""Main KA-BOL-AI GUI application window.

Wires together the assistant backend with customtkinter widgets.
Uses CTk.after() polling to safely bridge the voice thread and GUI thread.
"""

import logging
import sys
import threading
import time

import click
import customtkinter as ctk

from kabolai import __version__
from kabolai.gui.theme import (
    BG_DARK, BG_PANEL, BG_INPUT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    FONT_FAMILY, FONT_TITLE, FONT_BODY, FONT_SMALL,
    WINDOW_WIDTH, WINDOW_HEIGHT, PADDING, CORNER_RADIUS,
)
from kabolai.gui.widgets import (
    MicButton, StatusBanner, LanguageToggle, TranscriptBox,
)

logger = logging.getLogger(__name__)

# Polling interval (ms) for checking assistant state and events
POLL_INTERVAL = 100


class KabolaiApp(ctk.CTk):
    """Main application window for KA-BOL-AI."""

    def __init__(self, config=None, skip_assistant=False):
        super().__init__()

        # Window setup
        self.title(f"KA-BOL-AI v{__version__}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(400, 550)
        self.configure(fg_color=BG_DARK)

        # Dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._config = config
        self._assistant = None
        self._hotkey_mgr = None
        self._current_state = "ready"

        # Build UI
        self._build_ui()

        # Initialize assistant (unless skipped for testing)
        if not skip_assistant:
            self.after(200, self._initialize_assistant)

        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Create all UI widgets."""
        # ---- Top: Status banner + Language toggle ----
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=PADDING, pady=(PADDING, 0))

        self._status_banner = StatusBanner(top_frame)
        self._status_banner.pack(side="left", fill="x", expand=True)

        self._lang_toggle = LanguageToggle(
            top_frame, on_change=self._on_language_change,
        )
        self._lang_toggle.pack(side="right", padx=(PADDING, 0))

        # ---- Middle: Mic button ----
        mic_frame = ctk.CTkFrame(self, fg_color="transparent")
        mic_frame.pack(fill="x", pady=(20, 10))

        self._mic_button = MicButton(
            mic_frame, on_click=self._on_mic_click,
        )
        self._mic_button.pack()

        # ---- Listening mode toggle (Push-to-talk vs Continuous) ----
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=PADDING * 3, pady=(0, 10))

        self._mode_var = ctk.StringVar(value="push")
        self._mode_switch = ctk.CTkSegmentedButton(
            mode_frame,
            values=["Push-to-Talk", "Continuous"],
            variable=self._mode_var,
            font=FONT_BODY,
            fg_color=BG_PANEL,
            selected_color=TEXT_ACCENT,
            selected_hover_color="#0091ea",
            unselected_color=BG_INPUT,
            unselected_hover_color="#1a4a6e",
            corner_radius=8,
            command=self._on_mode_change,
        )
        self._mode_switch.pack(fill="x")
        self._mode_switch.set("Push-to-Talk")

        self._mode_hint = ctk.CTkLabel(
            mode_frame,
            text="Press Ctrl+Q or click mic to talk",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._mode_hint.pack(pady=(4, 0))

        # ---- Transcript box ----
        self._transcript = TranscriptBox(self)
        self._transcript.pack(
            fill="both", expand=True,
            padx=PADDING, pady=(0, PADDING),
        )

        # ---- Bottom bar ----
        bottom = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=CORNER_RADIUS, height=45)
        bottom.pack(fill="x", padx=PADDING, pady=(0, PADDING))
        bottom.pack_propagate(False)

        # Profile label
        profile_text = "CPU"
        if self._config:
            profile_text = self._config.profile.upper()
        self._profile_label = ctk.CTkLabel(
            bottom, text=f"Profile: {profile_text}",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._profile_label.pack(side="left", padx=PADDING)

        # Quit button
        quit_btn = ctk.CTkButton(
            bottom, text="Quit", width=70, height=28,
            font=FONT_SMALL, fg_color="#c62828", hover_color="#e53935",
            corner_radius=6,
            command=self._on_close,
        )
        quit_btn.pack(side="right", padx=PADDING, pady=8)

        # Mute button (toggle TTS voice on/off)
        self._muted = False
        self._mute_btn = ctk.CTkButton(
            bottom, text="\U0001F50A Voice", width=90, height=28,
            font=FONT_SMALL, fg_color="#2e7d32", hover_color="#388e3c",
            corner_radius=6,
            command=self._on_mute_toggle,
        )
        self._mute_btn.pack(side="right", padx=(0, 4), pady=8)

        # Settings button
        settings_btn = ctk.CTkButton(
            bottom, text="\u2699 Settings", width=90, height=28,
            font=FONT_SMALL, fg_color="#37474f", hover_color="#455a64",
            corner_radius=6,
            command=self._on_settings,
        )
        settings_btn.pack(side="right", padx=(0, 4), pady=8)

    def _initialize_assistant(self):
        """Initialize the assistant in a background thread to avoid freezing the GUI."""
        self._transcript.add_entry("system", "Initializing assistant...")
        self._status_banner.set_status("processing", self._get_language())

        def init():
            try:
                from kabolai.core.config import AppConfig
                from kabolai.core.logging import setup_logging
                from kabolai.assistant import Assistant
                from kabolai.gui.first_run import check_setup

                # Load config
                if self._config is None:
                    self._config = AppConfig.load()

                # Setup logging
                log_cfg = self._config.logging
                setup_logging(
                    level=log_cfg.get("level", "INFO"),
                    log_file=log_cfg.get("file", "kabolai.log"),
                )

                # Check first-run requirements
                missing = check_setup(self._config)
                if missing:
                    self.after(0, lambda: self._show_first_run(missing))
                    return

                # Create assistant
                assistant = Assistant(self._config)

                # Check brain
                if not assistant.check_brain():
                    self.after(0, lambda: self._transcript.add_entry(
                        "error",
                        "Ollama not reachable. Make sure it's running: ollama serve"
                    ))

                self._assistant = assistant

                # Setup hotkeys
                self._setup_hotkeys()

                self.after(0, self._on_assistant_ready)

            except Exception as e:
                logger.error(f"Init error: {e}", exc_info=True)
                self.after(0, lambda: self._on_init_error(str(e)))

        threading.Thread(target=init, daemon=True).start()

    def _on_assistant_ready(self):
        """Called on GUI thread when assistant is initialized."""
        lang = self._get_language()
        self._status_banner.set_status("ready", lang)
        self._lang_toggle.set_language(lang)
        self._mic_button.set_state("ready")
        self._transcript.add_entry("system", f"Ready! Language: {lang.upper()}")

        hotkey = "Ctrl+Q"
        if self._config:
            hotkey = self._config.hotkeys.push_to_talk.replace("+", "+").title()
        self._transcript.add_entry(
            "system", f"Press {hotkey} or click the mic button to talk."
        )

        # Start polling
        self.after(POLL_INTERVAL, self._poll)

    def _on_init_error(self, error_msg: str):
        """Called on GUI thread when initialization fails."""
        self._status_banner.set_status("error", "en")
        self._mic_button.set_state("inactive")
        self._transcript.add_entry("error", f"Init failed: {error_msg}")

    def _show_first_run(self, missing: dict):
        """Show the first-run wizard for missing components."""
        from kabolai.gui.first_run import FirstRunWizard
        wizard = FirstRunWizard(
            self, missing, self._config,
            on_complete=self._initialize_assistant,
        )

    def _setup_hotkeys(self):
        """Bind global hotkeys."""
        try:
            from kabolai.ui.hotkeys import HotkeyManager
            self._hotkey_mgr = HotkeyManager(self._config.hotkeys)
            self._hotkey_mgr.bind(
                on_push_to_talk=self._on_mic_click,
                on_toggle_active=self._on_toggle_active,
                on_toggle_language=self._on_toggle_language_hotkey,
                on_quit=lambda: self.after(0, self._on_close),
            )
        except Exception as e:
            logger.error(f"Hotkey binding failed: {e}")
            self.after(0, lambda: self._transcript.add_entry(
                "error", f"Hotkeys failed: {e}. Use the mic button instead."
            ))

    # ---- Polling ----

    def _poll(self):
        """Poll assistant state and events. Runs on GUI thread via after()."""
        if self._assistant is None:
            self.after(POLL_INTERVAL, self._poll)
            return

        # Read state
        state = self._assistant.state
        if not state.is_running:
            self._on_close()
            return

        # Determine visual state
        if not state.is_active:
            new_state = "inactive"
        elif state.is_speaking:
            new_state = "speaking"
        elif state.is_processing:
            new_state = "processing"
        elif state.is_listening:
            new_state = "listening"
        else:
            new_state = "ready"

        # Update widgets if state changed
        if new_state != self._current_state:
            self._current_state = new_state
            lang = self._get_language()
            self._status_banner.set_status(new_state, lang)
            self._mic_button.set_state(new_state)

        # Drain events
        for event in self._assistant.drain_events():
            self._handle_event(event)

        # Update language toggle
        self._lang_toggle.set_language(self._get_language())

        # Schedule next poll
        self.after(POLL_INTERVAL, self._poll)

    def _handle_event(self, event: dict):
        """Handle an assistant event on the GUI thread."""
        etype = event.get("type", "")
        data = event.get("data", {})

        if etype == "user_text":
            self._transcript.add_entry("user", data.get("text", ""))
        elif etype == "response_text":
            self._transcript.add_entry("assistant", data.get("text", ""))
        elif etype == "error":
            self._transcript.add_entry("error", data.get("message", "Unknown error"))
        elif etype == "status":
            pass  # Handled by state polling

    # ---- User Actions ----

    def _on_mode_change(self, value: str):
        """Switch between Push-to-Talk and Continuous listening modes."""
        if self._assistant is None:
            return

        if value == "Continuous":
            # Start always-listening mode
            self._assistant.start_continuous()
            self._mode_hint.configure(text="Listening always on — just speak naturally")
            self._mic_button._hint.configure(text="Always listening...")
            self._transcript.add_entry("system", "Continuous listening ON — just speak!")
        else:
            # Stop continuous, back to push-to-talk
            self._assistant.stop_continuous()
            hotkey = "Ctrl+Q"
            if self._config:
                hotkey = self._config.hotkeys.push_to_talk.replace("+", "+").title()
            self._mode_hint.configure(text=f"Press {hotkey} or click mic to talk")
            self._mic_button._hint.configure(text=f"Click or press {hotkey}")
            self._transcript.add_entry("system", "Push-to-Talk mode — press Ctrl+Q to speak")

    def _on_mic_click(self):
        """Handle mic button click or push-to-talk hotkey."""
        if self._assistant is None:
            return
        if not self._assistant.state.is_active:
            return

        # In continuous mode, mic click toggles continuous on/off
        if self._assistant.is_continuous:
            self._assistant.stop_continuous()
            self._mode_switch.set("Push-to-Talk")
            self._on_mode_change("Push-to-Talk")
            return

        # Push-to-talk: launch voice pipeline in background thread
        threading.Thread(
            target=self._assistant.handle_voice, daemon=True
        ).start()

    def _on_language_change(self, lang: str):
        """Handle language toggle click."""
        if self._assistant:
            self._assistant.state.set_language(lang)
            self._transcript.add_entry("system", f"Language: {lang.upper()}")

    def _on_toggle_language_hotkey(self):
        """Handle language toggle via hotkey."""
        if self._assistant:
            new_lang = self._assistant.state.toggle_language()
            self.after(0, lambda: self._lang_toggle.set_language(new_lang))
            self.after(0, lambda: self._transcript.add_entry(
                "system", f"Language: {new_lang.upper()}"
            ))

    def _on_toggle_active(self):
        """Handle toggle active via hotkey."""
        if self._assistant:
            new_state = self._assistant.state.toggle_active()
            if new_state:
                self._assistant.state.force_reset()
            status = "ACTIVE" if new_state else "INACTIVE"
            self.after(0, lambda: self._transcript.add_entry("system", f"[{status}]"))

    def _on_mute_toggle(self):
        """Toggle TTS voice on/off."""
        self._muted = not self._muted
        if self._assistant:
            self._assistant.tts_muted = self._muted

        if self._muted:
            self._mute_btn.configure(
                text="\U0001F507 Muted",
                fg_color="#c62828", hover_color="#e53935",
            )
            self._transcript.add_entry("system", "Voice muted")
        else:
            self._mute_btn.configure(
                text="\U0001F50A Voice",
                fg_color="#2e7d32", hover_color="#388e3c",
            )
            self._transcript.add_entry("system", "Voice unmuted")

    def _on_settings(self):
        """Open settings dialog."""
        try:
            from kabolai.gui.settings import SettingsDialog
            SettingsDialog(self, self._config, self._assistant)
        except Exception as e:
            logger.error(f"Settings error: {e}")

    def _on_close(self):
        """Clean shutdown."""
        if self._hotkey_mgr:
            try:
                self._hotkey_mgr.unbind_all()
            except Exception:
                pass

        if self._assistant:
            try:
                self._assistant.shutdown()
            except Exception:
                pass

        self.quit()
        self.destroy()

    # ---- Helpers ----

    def _get_language(self) -> str:
        if self._assistant:
            return self._assistant.state.language
        if self._config:
            return self._config.language
        return "en"


def main(config=None, profile=None, language=None):
    """Launch the KA-BOL-AI GUI application."""
    from kabolai.core.config import AppConfig

    try:
        app_config = config or AppConfig.load(profile=profile)
        if language:
            app_config.language = language
    except Exception as e:
        print(f"Config error: {e}")
        sys.exit(1)

    app = KabolaiApp(config=app_config)
    app.mainloop()


if __name__ == "__main__":
    main()
