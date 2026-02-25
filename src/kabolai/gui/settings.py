"""Settings dialog for KA-BOL-AI GUI.

Allows users to change profile, voice, hotkeys, and audio settings.
"""

import logging
import tkinter as tk

import customtkinter as ctk

from kabolai.gui.theme import (
    BG_DARK, BG_PANEL, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    GREEN, YELLOW,
    FONT_FAMILY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL,
    PADDING, CORNER_RADIUS,
)

logger = logging.getLogger(__name__)


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""

    def __init__(self, parent, config=None, assistant=None):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("420x480")
        self.configure(fg_color=BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._config = config
        self._assistant = assistant
        self._parent = parent

        self._build_ui()

    def _build_ui(self):
        # Title
        ctk.CTkLabel(
            self, text="Settings",
            font=FONT_TITLE, text_color=TEXT_ACCENT,
        ).pack(pady=(20, 15))

        # Scrollable settings area
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_PANEL, corner_radius=CORNER_RADIUS,
        )
        scroll.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        # ---- Profile ----
        self._add_section(scroll, "Hardware Profile")
        profiles = ["cpu", "gpu_light", "gpu_full"]
        current_profile = self._config.profile if self._config else "cpu"
        self._profile_var = ctk.StringVar(value=current_profile)
        profile_menu = ctk.CTkOptionMenu(
            scroll, values=profiles, variable=self._profile_var,
            font=FONT_BODY, fg_color=BG_INPUT,
            button_color=TEXT_ACCENT, button_hover_color="#0091ea",
            dropdown_fg_color=BG_INPUT,
            width=200,
        )
        profile_menu.pack(anchor="w", padx=PADDING, pady=(0, 10))

        ctk.CTkLabel(
            scroll,
            text="Note: Profile change requires restart.",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=PADDING, pady=(0, 10))

        # ---- Hotkeys ----
        self._add_section(scroll, "Hotkeys")
        hotkeys = {
            "Push to Talk": self._config.hotkeys.push_to_talk if self._config else "ctrl+q",
            "Toggle Active": self._config.hotkeys.toggle_active if self._config else "ctrl+shift+a",
            "Switch Language": self._config.hotkeys.toggle_language if self._config else "ctrl+shift+l",
            "Quit": self._config.hotkeys.quit if self._config else "ctrl+shift+x",
        }
        for label, key in hotkeys.items():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=PADDING, pady=2)
            ctk.CTkLabel(
                row, text=f"{label}:", font=FONT_BODY,
                text_color=TEXT_PRIMARY, width=130, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=key, font=FONT_BODY,
                text_color=TEXT_ACCENT, anchor="w",
            ).pack(side="left")

        ctk.CTkLabel(
            scroll,
            text="Edit config/default.yaml to change hotkeys.",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=PADDING, pady=(4, 10))

        # ---- Audio ----
        self._add_section(scroll, "Audio")

        # List audio devices
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            inputs = [d for d in devices if d["max_input_channels"] > 0]
            if inputs:
                ctk.CTkLabel(
                    scroll, text="Input devices:",
                    font=FONT_SMALL, text_color=TEXT_SECONDARY,
                ).pack(anchor="w", padx=PADDING, pady=(0, 2))
                for d in inputs[:5]:
                    ctk.CTkLabel(
                        scroll, text=f"  \u2022 {d['name']}",
                        font=FONT_SMALL, text_color=TEXT_PRIMARY,
                    ).pack(anchor="w", padx=PADDING)
        except Exception:
            ctk.CTkLabel(
                scroll, text="Could not list audio devices.",
                font=FONT_SMALL, text_color=YELLOW,
            ).pack(anchor="w", padx=PADDING)

        # ---- LLM ----
        self._add_section(scroll, "LLM (Ollama)")
        ollama_cfg = self._config.brain.get("ollama", {}) if self._config else {}
        model_name = ollama_cfg.get("model", "qwen2.5:1.5b")
        base_url = ollama_cfg.get("base_url", "http://localhost:11434")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=PADDING, pady=2)
        ctk.CTkLabel(row, text="Model:", font=FONT_BODY, text_color=TEXT_PRIMARY, width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=model_name, font=FONT_BODY, text_color=TEXT_ACCENT).pack(side="left")

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", padx=PADDING, pady=2)
        ctk.CTkLabel(row2, text="Server:", font=FONT_BODY, text_color=TEXT_PRIMARY, width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(row2, text=base_url, font=FONT_BODY, text_color=TEXT_ACCENT).pack(side="left")

        # Check Ollama status
        status_text = "Checking..."
        status_color = TEXT_SECONDARY
        try:
            import requests
            r = requests.get(f"{base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                status_text = f"Connected ({len(models)} models)"
                status_color = GREEN
            else:
                status_text = "Not responding"
                status_color = YELLOW
        except Exception:
            status_text = "Not connected"
            status_color = YELLOW

        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", padx=PADDING, pady=(2, 10))
        ctk.CTkLabel(row3, text="Status:", font=FONT_BODY, text_color=TEXT_PRIMARY, width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(row3, text=status_text, font=FONT_BODY, text_color=status_color).pack(side="left")

        # ---- Bottom buttons ----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=PADDING, pady=PADDING)

        ctk.CTkButton(
            btn_frame, text="Close", width=100, height=32,
            font=FONT_BODY, fg_color="#37474f", hover_color="#455a64",
            corner_radius=6,
            command=self._close,
        ).pack(side="right")

    def _add_section(self, parent, title: str):
        """Add a section header."""
        ctk.CTkLabel(
            parent, text=title,
            font=FONT_HEADING, text_color=TEXT_ACCENT,
        ).pack(anchor="w", padx=PADDING, pady=(12, 4))

    def _close(self):
        self.grab_release()
        self.destroy()
