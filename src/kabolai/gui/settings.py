"""Settings dialog with STT/TTS model selectors.

Users can choose STT quality level (VOSK small -> Whisper large)
and TTS voice, and changes apply live without restarting.
"""

import logging
import threading
import tkinter as tk

import customtkinter as ctk

from kabolai.gui.theme import (
    BG_DARK, BG_PANEL, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    GREEN, YELLOW, RED, BLUE,
    FONT_FAMILY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL,
    PADDING, CORNER_RADIUS,
)

logger = logging.getLogger(__name__)

# STT models from worst to best, with VRAM/description info
STT_MODELS = [
    {
        "id": "vosk_small",
        "label": "VOSK Small (CPU)",
        "desc": "Fast, low accuracy (~15-20% WER). No GPU needed.",
        "engine": "vosk",
        "needs_gpu": False,
        "vram_mb": 0,
    },
    {
        "id": "whisper_tiny",
        "label": "Whisper Tiny (GPU)",
        "desc": "Fast GPU, decent accuracy (~10% WER). ~150MB VRAM.",
        "engine": "whisper",
        "model_size": "tiny",
        "needs_gpu": True,
        "vram_mb": 150,
    },
    {
        "id": "whisper_base",
        "label": "Whisper Base (GPU)",
        "desc": "Good balance of speed and accuracy (~8% WER). ~300MB VRAM.",
        "engine": "whisper",
        "model_size": "base",
        "needs_gpu": True,
        "vram_mb": 300,
    },
    {
        "id": "whisper_small",
        "label": "Whisper Small (GPU)",
        "desc": "Very good accuracy (~5% WER). ~500MB VRAM.",
        "engine": "whisper",
        "model_size": "small",
        "needs_gpu": True,
        "vram_mb": 500,
    },
    {
        "id": "whisper_medium",
        "label": "Whisper Medium (GPU) \u2b50",
        "desc": "Excellent accuracy (~3-4% WER). Best for RTX 4070. ~1.5GB VRAM.",
        "engine": "whisper",
        "model_size": "medium",
        "needs_gpu": True,
        "vram_mb": 1500,
    },
    {
        "id": "whisper_large",
        "label": "Whisper Large-v3 (GPU)",
        "desc": "Best accuracy (~2-3% WER). Needs 8GB+ VRAM. ~3GB VRAM.",
        "engine": "whisper",
        "model_size": "large-v3",
        "needs_gpu": True,
        "vram_mb": 3000,
    },
]

# Ukrainian TTS voices
UK_VOICES = ["Dmytro", "Tetiana", "Oleksa", "Lada", "Mykyta"]


def _get_current_stt_id(config) -> str:
    """Determine current STT model ID from config."""
    if not config:
        return "vosk_small"
    engine = config.stt.get("engine", "vosk")
    if engine == "whisper":
        size = config.stt.get("whisper", {}).get("model_size", "base")
        return f"whisper_{size}"
    return "vosk_small"


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog with STT/TTS model selectors."""

    def __init__(self, parent, config=None, assistant=None):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("480x680")
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
            self, text="\u2699 Settings",
            font=FONT_TITLE, text_color=TEXT_ACCENT,
        ).pack(pady=(15, 10))

        # Scrollable settings area
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_PANEL, corner_radius=CORNER_RADIUS,
        )
        scroll.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        # ==========================================
        # SPEECH-TO-TEXT (STT) Model Selector
        # ==========================================
        self._add_section(scroll, "\U0001F3A4 Speech Recognition (STT)")

        ctk.CTkLabel(
            scroll,
            text="Choose recognition quality. Better models need GPU\n"
                 "but understand you much more accurately.",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
            wraplength=400, justify="left",
        ).pack(anchor="w", padx=PADDING, pady=(0, 8))

        # Current selection
        current_stt = _get_current_stt_id(self._config)
        stt_labels = [m["label"] for m in STT_MODELS]
        current_label = next(
            (m["label"] for m in STT_MODELS if m["id"] == current_stt),
            stt_labels[0]
        )

        self._stt_var = ctk.StringVar(value=current_label)
        stt_menu = ctk.CTkOptionMenu(
            scroll, values=stt_labels, variable=self._stt_var,
            font=FONT_BODY, fg_color=BG_INPUT,
            button_color=TEXT_ACCENT, button_hover_color="#0091ea",
            dropdown_fg_color=BG_INPUT,
            width=350,
            command=self._on_stt_change,
        )
        stt_menu.pack(anchor="w", padx=PADDING, pady=(0, 4))

        # Description label (updates when selection changes)
        self._stt_desc = ctk.CTkLabel(
            scroll, text="", font=FONT_SMALL,
            text_color=TEXT_SECONDARY, wraplength=400, justify="left",
        )
        self._stt_desc.pack(anchor="w", padx=PADDING, pady=(0, 4))

        # Status label (shows loading/download progress)
        self._stt_status = ctk.CTkLabel(
            scroll, text="", font=FONT_SMALL,
            text_color=GREEN,
        )
        self._stt_status.pack(anchor="w", padx=PADDING, pady=(0, 8))

        # Apply button for STT
        self._stt_apply_btn = ctk.CTkButton(
            scroll, text="Apply STT Model", width=160, height=30,
            font=FONT_BODY, fg_color=GREEN, hover_color="#00c853",
            text_color="black", corner_radius=6,
            command=self._apply_stt,
        )
        self._stt_apply_btn.pack(anchor="w", padx=PADDING, pady=(0, 12))

        # Trigger initial description
        self._on_stt_change(current_label)

        # ==========================================
        # TEXT-TO-SPEECH (TTS)
        # ==========================================
        self._add_section(scroll, "\U0001F5E3 Text-to-Speech (TTS)")

        # Ukrainian voice selector
        ctk.CTkLabel(
            scroll, text="Ukrainian voice:",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PADDING, pady=(0, 4))

        current_uk_voice = "Dmytro"
        if self._config:
            current_uk_voice = self._config.tts.get("ukrainian", {}).get("voice", "Dmytro")

        self._uk_voice_var = ctk.StringVar(value=current_uk_voice)
        uk_menu = ctk.CTkOptionMenu(
            scroll, values=UK_VOICES, variable=self._uk_voice_var,
            font=FONT_BODY, fg_color=BG_INPUT,
            button_color=TEXT_ACCENT, button_hover_color="#0091ea",
            dropdown_fg_color=BG_INPUT,
            width=200,
        )
        uk_menu.pack(anchor="w", padx=PADDING, pady=(0, 4))

        ctk.CTkLabel(
            scroll,
            text="Voices: Dmytro (male), Tetiana (female),\n"
                 "Oleksa (male), Lada (female), Mykyta (male)",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
            justify="left",
        ).pack(anchor="w", padx=PADDING, pady=(0, 4))

        # English TTS speed
        ctk.CTkLabel(
            scroll, text="English speech rate:",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PADDING, pady=(8, 4))

        current_rate = 175
        if self._config:
            current_rate = self._config.tts.get("english", {}).get("pyttsx3", {}).get("rate", 175)

        self._en_rate_var = ctk.IntVar(value=current_rate)
        rate_slider = ctk.CTkSlider(
            scroll, from_=100, to=300,
            variable=self._en_rate_var,
            width=300,
            fg_color=BG_INPUT,
            progress_color=TEXT_ACCENT,
        )
        rate_slider.pack(anchor="w", padx=PADDING, pady=(0, 2))

        self._rate_label = ctk.CTkLabel(
            scroll, text=f"{current_rate} words/min",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._rate_label.pack(anchor="w", padx=PADDING, pady=(0, 4))
        rate_slider.configure(command=lambda v: self._rate_label.configure(
            text=f"{int(float(v))} words/min"
        ))

        # Apply TTS button
        ctk.CTkButton(
            scroll, text="Apply TTS Settings", width=160, height=30,
            font=FONT_BODY, fg_color=GREEN, hover_color="#00c853",
            text_color="black", corner_radius=6,
            command=self._apply_tts,
        ).pack(anchor="w", padx=PADDING, pady=(4, 12))

        # ==========================================
        # HOTKEYS (read-only display)
        # ==========================================
        self._add_section(scroll, "\u2328 Hotkeys")
        hotkeys = {
            "Push to Talk": self._config.hotkeys.push_to_talk if self._config else "ctrl+q",
            "Toggle Active": self._config.hotkeys.toggle_active if self._config else "ctrl+shift+a",
            "Switch Language": self._config.hotkeys.toggle_language if self._config else "ctrl+shift+l",
            "Quit": self._config.hotkeys.quit if self._config else "ctrl+shift+x",
        }
        for label, key in hotkeys.items():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=PADDING, pady=1)
            ctk.CTkLabel(
                row, text=f"{label}:", font=FONT_SMALL,
                text_color=TEXT_PRIMARY, width=120, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=key, font=FONT_SMALL,
                text_color=TEXT_ACCENT, anchor="w",
            ).pack(side="left")

        # ==========================================
        # LLM STATUS
        # ==========================================
        self._add_section(scroll, "\U0001F9E0 LLM (Ollama)")
        ollama_cfg = self._config.brain.get("ollama", {}) if self._config else {}
        model_name = ollama_cfg.get("model", "qwen2.5:1.5b")
        base_url = ollama_cfg.get("base_url", "http://localhost:11434")

        # Check Ollama status
        status_text = "Checking..."
        status_color = TEXT_SECONDARY
        try:
            import requests
            r = requests.get(f"{base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                status_text = f"\u2705 Connected | Model: {model_name} | {len(models)} loaded"
                status_color = GREEN
            else:
                status_text = "\u26a0 Not responding"
                status_color = YELLOW
        except Exception:
            status_text = "\u274c Not connected — run: ollama serve"
            status_color = YELLOW

        ctk.CTkLabel(
            scroll, text=status_text, font=FONT_SMALL,
            text_color=status_color, wraplength=400, justify="left",
        ).pack(anchor="w", padx=PADDING, pady=(0, 12))

        # ---- Bottom buttons ----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=PADDING, pady=PADDING)

        ctk.CTkButton(
            btn_frame, text="Close", width=100, height=32,
            font=FONT_BODY, fg_color="#37474f", hover_color="#455a64",
            corner_radius=6,
            command=self._close,
        ).pack(side="right")

    # ---- STT Model Selection ----

    def _on_stt_change(self, label: str):
        """Update description when STT model selection changes."""
        model = next((m for m in STT_MODELS if m["label"] == label), None)
        if model:
            self._stt_desc.configure(text=model["desc"])
            # Check GPU availability for whisper models
            if model["needs_gpu"]:
                try:
                    import ctranslate2
                    gpu_count = ctranslate2.get_cuda_device_count()
                    if gpu_count > 0:
                        self._stt_status.configure(
                            text=f"\u2705 GPU detected ({gpu_count} CUDA device(s))",
                            text_color=GREEN,
                        )
                    else:
                        self._stt_status.configure(
                            text="\u26a0 No GPU — will be slow on CPU",
                            text_color=YELLOW,
                        )
                except ImportError:
                    self._stt_status.configure(
                        text="\u274c faster-whisper not installed. Run: pip install faster-whisper",
                        text_color=RED,
                    )
            else:
                self._stt_status.configure(text="\u2705 Runs on CPU (no GPU needed)", text_color=GREEN)

    def _apply_stt(self):
        """Apply the selected STT model. Reloads the engine live."""
        label = self._stt_var.get()
        model = next((m for m in STT_MODELS if m["label"] == label), None)
        if not model:
            return

        self._stt_apply_btn.configure(state="disabled", text="Loading...")
        self._stt_status.configure(text="Loading model... please wait", text_color=BLUE)

        def apply():
            try:
                if model["engine"] == "whisper":
                    # Check if faster-whisper is available
                    try:
                        from faster_whisper import WhisperModel  # noqa: F401
                    except ImportError:
                        self.after(0, lambda: self._stt_status.configure(
                            text="\u274c Install first: pip install faster-whisper",
                            text_color=RED,
                        ))
                        self.after(0, lambda: self._stt_apply_btn.configure(
                            state="normal", text="Apply STT Model",
                        ))
                        return

                    # Update config
                    self._config.stt["engine"] = "whisper"
                    self._config.stt.setdefault("whisper", {})
                    self._config.stt["whisper"]["model_size"] = model["model_size"]

                    # Detect GPU
                    try:
                        import ctranslate2
                        if ctranslate2.get_cuda_device_count() > 0:
                            self._config.stt["whisper"]["device"] = "cuda"
                            self._config.stt["whisper"]["compute_type"] = "float16"
                        else:
                            self._config.stt["whisper"]["device"] = "cpu"
                            self._config.stt["whisper"]["compute_type"] = "int8"
                    except Exception:
                        self._config.stt["whisper"]["device"] = "cpu"
                        self._config.stt["whisper"]["compute_type"] = "int8"

                else:
                    # VOSK
                    self._config.stt["engine"] = "vosk"

                # Reload STT engine in the assistant
                if self._assistant:
                    from kabolai.stt.factory import create_stt_engine
                    old_stt = self._assistant.stt
                    new_stt = create_stt_engine(self._config)
                    self._assistant.stt = new_stt
                    old_stt.cleanup()

                self.after(0, lambda: self._stt_status.configure(
                    text=f"\u2705 Loaded: {model['label']}",
                    text_color=GREEN,
                ))
            except Exception as e:
                logger.error(f"STT apply error: {e}", exc_info=True)
                self.after(0, lambda: self._stt_status.configure(
                    text=f"\u274c Error: {e}",
                    text_color=RED,
                ))
            finally:
                self.after(0, lambda: self._stt_apply_btn.configure(
                    state="normal", text="Apply STT Model",
                ))

        threading.Thread(target=apply, daemon=True).start()

    # ---- TTS Settings ----

    def _apply_tts(self):
        """Apply TTS voice and speed settings."""
        if not self._assistant:
            return

        # Update Ukrainian voice
        new_voice = self._uk_voice_var.get()
        if self._config:
            self._config.tts.setdefault("ukrainian", {})["voice"] = new_voice

        # Reload Ukrainian TTS if it was loaded
        if self._assistant._tts_uk:
            try:
                self._assistant._tts_uk.set_voice(new_voice)
            except Exception as e:
                logger.error(f"Ukrainian voice change error: {e}")

        # Update English speech rate
        new_rate = int(self._en_rate_var.get())
        if self._assistant._tts_en:
            try:
                self._assistant._tts_en.set_speed(new_rate / 175.0)
            except Exception as e:
                logger.error(f"English rate change error: {e}")

    # ---- Helpers ----

    def _add_section(self, parent, title: str):
        """Add a section header."""
        ctk.CTkLabel(
            parent, text=title,
            font=FONT_HEADING, text_color=TEXT_ACCENT,
        ).pack(anchor="w", padx=PADDING, pady=(12, 4))

    def _close(self):
        self.grab_release()
        self.destroy()
