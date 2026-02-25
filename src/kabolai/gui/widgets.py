"""Custom widgets for the KA-BOL-AI GUI.

MicButton — big round microphone button (changes color by state)
StatusBanner — top bar showing status and language toggle
TranscriptBox — scrollable transcript log with color-coded entries
LanguageToggle — EN/UK language switcher buttons
"""

import time
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from kabolai.gui.theme import (
    BG_DARK, BG_PANEL, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    BORDER, GREEN, RED, BLUE, PURPLE, GREY, YELLOW,
    MIC_READY, MIC_LISTENING, MIC_PROCESSING, MIC_SPEAKING, MIC_INACTIVE,
    FONT_FAMILY, FONT_HEADING, FONT_BODY, FONT_SMALL,
    FONT_TRANSCRIPT, FONT_MIC_HINT,
    MIC_BUTTON_SIZE, PADDING, CORNER_RADIUS,
    STATUS_TEXT,
)


class MicButton(ctk.CTkFrame):
    """Large round microphone button that changes color based on state.

    States: ready (green), listening (red), processing (blue),
            speaking (purple), inactive (grey)
    """

    def __init__(self, parent, on_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_click = on_click
        self._state = "ready"

        # Canvas for the round button
        size = MIC_BUTTON_SIZE + 20
        self._canvas = tk.Canvas(
            self, width=size, height=size,
            bg=BG_DARK, highlightthickness=0,
        )
        self._canvas.pack(pady=5)

        # Draw outer glow ring
        margin = 5
        self._glow = self._canvas.create_oval(
            margin, margin, size - margin, size - margin,
            fill="", outline=MIC_READY, width=3,
        )

        # Draw main circle
        inner = 15
        self._circle = self._canvas.create_oval(
            inner, inner, size - inner, size - inner,
            fill=MIC_READY, outline="",
        )

        # Mic icon (Unicode microphone)
        self._mic_text = self._canvas.create_text(
            size // 2, size // 2,
            text="\U0001F3A4",  # Microphone emoji
            font=(FONT_FAMILY, 32),
            fill="white",
        )

        # Hint text below
        self._hint = ctk.CTkLabel(
            self, text="Click or press Ctrl+Q",
            font=FONT_MIC_HINT, text_color=TEXT_SECONDARY,
        )
        self._hint.pack(pady=(0, 5))

        # Bind click
        self._canvas.bind("<Button-1>", self._handle_click)
        # Pulse animation
        self._pulse_id = None

    def _handle_click(self, event=None):
        if self._on_click and self._state in ("ready", "inactive"):
            self._on_click()

    def set_state(self, state: str):
        """Set button visual state: ready, listening, processing, speaking, inactive."""
        self._state = state
        colors = {
            "ready": MIC_READY,
            "listening": MIC_LISTENING,
            "processing": MIC_PROCESSING,
            "speaking": MIC_SPEAKING,
            "inactive": MIC_INACTIVE,
        }
        color = colors.get(state, MIC_READY)
        self._canvas.itemconfig(self._circle, fill=color)
        self._canvas.itemconfig(self._glow, outline=color)

        # Start/stop pulse animation
        if state in ("listening", "processing", "speaking"):
            self._start_pulse(color)
        else:
            self._stop_pulse()

    def _start_pulse(self, color: str):
        """Gentle pulse animation for active states."""
        if self._pulse_id is not None:
            return  # Already pulsing

        def pulse(step=0):
            if self._state not in ("listening", "processing", "speaking"):
                self._stop_pulse()
                return
            # Alternate glow width between 2 and 5
            width = 3 + 2 * abs((step % 20) - 10) / 10
            self._canvas.itemconfig(self._glow, width=width)
            self._pulse_id = self.after(80, lambda: pulse(step + 1))

        pulse()

    def _stop_pulse(self):
        if self._pulse_id is not None:
            self.after_cancel(self._pulse_id)
            self._pulse_id = None
        self._canvas.itemconfig(self._glow, width=3)


class StatusBanner(ctk.CTkFrame):
    """Top status bar showing current state and language."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent, fg_color=BG_PANEL,
            corner_radius=CORNER_RADIUS,
            height=45, **kwargs,
        )
        self.pack_propagate(False)

        # Status dot + text
        self._status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._status_frame.pack(side="left", padx=PADDING, pady=8)

        self._dot = ctk.CTkLabel(
            self._status_frame, text="\u25CF",
            font=(FONT_FAMILY, 16), text_color=GREEN, width=20,
        )
        self._dot.pack(side="left")

        self._status_label = ctk.CTkLabel(
            self._status_frame, text="Ready",
            font=FONT_HEADING, text_color=TEXT_PRIMARY,
        )
        self._status_label.pack(side="left", padx=(4, 0))

    def set_status(self, state: str, language: str = "en"):
        """Update status display."""
        status_info = STATUS_TEXT.get(state, STATUS_TEXT["ready"])
        text = status_info.get(language, status_info.get("en", "Ready"))
        colors = {
            "ready": GREEN,
            "listening": RED,
            "processing": BLUE,
            "speaking": PURPLE,
            "inactive": GREY,
            "error": YELLOW,
        }
        color = colors.get(state, GREEN)
        self._dot.configure(text_color=color)
        self._status_label.configure(text=text)


class LanguageToggle(ctk.CTkFrame):
    """EN/UK language toggle buttons."""

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._current = "en"

        self._en_btn = ctk.CTkButton(
            self, text="EN", width=50, height=30,
            font=FONT_BODY,
            fg_color=TEXT_ACCENT, hover_color=BLUE,
            text_color="white",
            corner_radius=6,
            command=lambda: self._select("en"),
        )
        self._en_btn.pack(side="left", padx=2)

        self._uk_btn = ctk.CTkButton(
            self, text="UK", width=50, height=30,
            font=FONT_BODY,
            fg_color=BG_INPUT, hover_color=BLUE,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            command=lambda: self._select("uk"),
        )
        self._uk_btn.pack(side="left", padx=2)

    def _select(self, lang: str):
        if lang == self._current:
            return
        self._current = lang
        self._update_visual()
        if self._on_change:
            self._on_change(lang)

    def set_language(self, lang: str):
        """Update the toggle without triggering callback."""
        self._current = lang
        self._update_visual()

    def _update_visual(self):
        if self._current == "en":
            self._en_btn.configure(fg_color=TEXT_ACCENT, text_color="white")
            self._uk_btn.configure(fg_color=BG_INPUT, text_color=TEXT_SECONDARY)
        else:
            self._en_btn.configure(fg_color=BG_INPUT, text_color=TEXT_SECONDARY)
            self._uk_btn.configure(fg_color=TEXT_ACCENT, text_color="white")


class TranscriptBox(ctk.CTkFrame):
    """Scrollable transcript log with color-coded entries."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent, fg_color=BG_PANEL,
            corner_radius=CORNER_RADIUS, **kwargs,
        )

        # Header
        header = ctk.CTkLabel(
            self, text="Transcript",
            font=FONT_HEADING, text_color=TEXT_ACCENT,
            anchor="w",
        )
        header.pack(fill="x", padx=PADDING, pady=(8, 4))

        # Scrollable text area
        self._textbox = ctk.CTkTextbox(
            self, font=FONT_TRANSCRIPT,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            corner_radius=6,
            wrap="word",
            state="disabled",
        )
        self._textbox.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        # Configure color tags
        self._textbox.tag_config("user", foreground=GREEN)
        self._textbox.tag_config("assistant", foreground=TEXT_ACCENT)
        self._textbox.tag_config("timestamp", foreground=TEXT_SECONDARY)
        self._textbox.tag_config("error", foreground=YELLOW)
        self._textbox.tag_config("system", foreground=GREY)

    def add_entry(self, role: str, text: str, timestamp: str = None):
        """Add a transcript entry.

        role: 'user', 'assistant', 'error', 'system'
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")

        prefix_map = {
            "user": "> You: ",
            "assistant": "< AI: ",
            "error": "! Error: ",
            "system": "* ",
        }
        prefix = prefix_map.get(role, "> ")
        tag = role if role in ("user", "assistant", "error", "system") else "user"

        self._textbox.configure(state="normal")
        self._textbox.insert("end", f"[{timestamp}] ", "timestamp")
        self._textbox.insert("end", f"{prefix}{text}\n", tag)
        self._textbox.configure(state="disabled")
        self._textbox.see("end")

    def clear(self):
        """Clear all transcript entries."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
