"""First-run wizard: checks for VOSK models, Ollama, and LLM model.

Provides a setup wizard with progress bars for downloading missing components.
"""

import logging
import os
import shutil
import threading
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from kabolai.core.config import AppConfig
from kabolai.core.constants import VOSK_MODEL_URLS, MODELS_DIR
from kabolai.gui.theme import (
    BG_DARK, BG_PANEL, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    GREEN, RED, YELLOW, BLUE,
    FONT_FAMILY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL,
    PADDING, CORNER_RADIUS,
)

logger = logging.getLogger(__name__)


def check_setup(config: AppConfig) -> dict:
    """Check if all required components are available.

    Returns a dict of missing components (empty if all good):
    {
        "vosk_en": True,   # Missing EN VOSK model
        "vosk_uk": True,   # Missing UK VOSK model
        "ollama": True,    # Ollama not running
        "llm_model": True, # LLM model not pulled
    }
    """
    missing = {}
    profile = config.profile

    # Check VOSK models (they live at models/vosk/en/ and models/vosk/uk/)
    vosk_urls = VOSK_MODEL_URLS.get(profile, VOSK_MODEL_URLS.get("cpu", {}))
    for lang in ("en", "uk"):
        model_dir = MODELS_DIR / "vosk" / lang
        if not model_dir.exists() or not any(model_dir.iterdir()):
            missing[f"vosk_{lang}"] = True

    # Check Ollama
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            ollama_cfg = config.brain.get("ollama", {})
            needed_model = ollama_cfg.get("model", "qwen2.5:1.5b")
            # Check if model (or variant) is available
            has_model = any(
                needed_model in m or m.startswith(needed_model.split(":")[0])
                for m in models
            )
            if not has_model:
                missing["llm_model"] = True
        else:
            missing["ollama"] = True
    except Exception:
        missing["ollama"] = True

    return missing


class FirstRunWizard(ctk.CTkToplevel):
    """Setup wizard that downloads missing models."""

    def __init__(self, parent, missing: dict, config: AppConfig, on_complete=None):
        super().__init__(parent)
        self.title("KA-BOL-AI Setup")
        self.geometry("480x500")
        self.configure(fg_color=BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._missing = missing
        self._config = config
        self._on_complete = on_complete
        self._downloads_done = 0
        self._downloads_total = 0

        self._build_ui()

    def _build_ui(self):
        # Title
        title = ctk.CTkLabel(
            self, text="First-Time Setup",
            font=FONT_TITLE, text_color=TEXT_ACCENT,
        )
        title.pack(pady=(20, 10))

        desc = ctk.CTkLabel(
            self, text="KA-BOL-AI needs to download some components.\n"
                       "This only happens once.",
            font=FONT_BODY, text_color=TEXT_SECONDARY,
            wraplength=400,
        )
        desc.pack(pady=(0, 20))

        # Scrollable frame for items
        self._items_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_PANEL, corner_radius=CORNER_RADIUS,
        )
        self._items_frame.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        self._progress_widgets = {}

        # VOSK models
        for lang in ("en", "uk"):
            key = f"vosk_{lang}"
            if key in self._missing:
                self._add_download_item(
                    key, f"VOSK Model ({lang.upper()})",
                    "Speech recognition model",
                )
                self._downloads_total += 1

        # Ollama
        if "ollama" in self._missing:
            self._add_info_item(
                "ollama", "Ollama (LLM Runtime)",
                "Ollama is not running. Please install and start it.",
                link="https://ollama.ai/download",
            )

        # LLM model
        if "llm_model" in self._missing:
            ollama_cfg = self._config.brain.get("ollama", {})
            model_name = ollama_cfg.get("model", "qwen2.5:1.5b")
            self._add_download_item(
                "llm_model", f"LLM Model ({model_name})",
                f"Language model for understanding commands",
            )
            self._downloads_total += 1

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=PADDING, pady=PADDING)

        self._start_btn = ctk.CTkButton(
            btn_frame, text="Download All", width=140, height=36,
            font=FONT_BODY, fg_color=GREEN, hover_color="#00c853",
            text_color="black", corner_radius=8,
            command=self._start_downloads,
        )
        self._start_btn.pack(side="right")

        if "ollama" in self._missing:
            check_btn = ctk.CTkButton(
                btn_frame, text="Check Again", width=120, height=36,
                font=FONT_BODY, fg_color=BLUE, hover_color="#448aff",
                corner_radius=8,
                command=self._check_ollama,
            )
            check_btn.pack(side="right", padx=(0, 8))

    def _add_download_item(self, key: str, title: str, description: str):
        """Add a downloadable item with progress bar."""
        frame = ctk.CTkFrame(self._items_frame, fg_color=BG_INPUT, corner_radius=8)
        frame.pack(fill="x", pady=4, padx=4)

        ctk.CTkLabel(
            frame, text=title, font=FONT_HEADING, text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            frame, text=description, font=FONT_SMALL, text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=10, pady=(0, 4))

        progress = ctk.CTkProgressBar(
            frame, fg_color=BG_PANEL, progress_color=TEXT_ACCENT,
            corner_radius=4, height=12,
        )
        progress.pack(fill="x", padx=10, pady=(0, 4))
        progress.set(0)

        status_label = ctk.CTkLabel(
            frame, text="Pending", font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        status_label.pack(anchor="w", padx=10, pady=(0, 8))

        self._progress_widgets[key] = {
            "progress": progress,
            "status": status_label,
        }

    def _add_info_item(self, key: str, title: str, description: str, link: str = None):
        """Add an informational item (not downloadable)."""
        frame = ctk.CTkFrame(self._items_frame, fg_color=BG_INPUT, corner_radius=8)
        frame.pack(fill="x", pady=4, padx=4)

        ctk.CTkLabel(
            frame, text=title, font=FONT_HEADING, text_color=YELLOW,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            frame, text=description, font=FONT_SMALL, text_color=TEXT_SECONDARY,
            wraplength=380,
        ).pack(anchor="w", padx=10, pady=(0, 4))

        if link:
            link_btn = ctk.CTkButton(
                frame, text=f"Download: {link}", width=300, height=28,
                font=FONT_SMALL, fg_color="#37474f", hover_color="#455a64",
                corner_radius=4,
                command=lambda: self._open_link(link),
            )
            link_btn.pack(anchor="w", padx=10, pady=(0, 8))

    def _open_link(self, url: str):
        import webbrowser
        webbrowser.open(url)

    def _start_downloads(self):
        self._start_btn.configure(state="disabled", text="Downloading...")
        threading.Thread(target=self._run_downloads, daemon=True).start()

    def _run_downloads(self):
        """Download all missing components."""
        profile = self._config.profile

        # Download VOSK models
        for lang in ("en", "uk"):
            key = f"vosk_{lang}"
            if key not in self._missing:
                continue
            self._update_status(key, "Downloading...", 0)
            try:
                self._download_vosk(lang, profile, key)
                self._update_status(key, "Done!", 1.0)
            except Exception as e:
                self._update_status(key, f"Error: {e}", 0)
                logger.error(f"VOSK download error ({lang}): {e}", exc_info=True)

        # Pull LLM model
        if "llm_model" in self._missing and "ollama" not in self._missing:
            key = "llm_model"
            self._update_status(key, "Pulling model...", 0.1)
            try:
                self._pull_ollama_model(key)
                self._update_status(key, "Done!", 1.0)
            except Exception as e:
                self._update_status(key, f"Error: {e}", 0)
                logger.error(f"Ollama pull error: {e}", exc_info=True)

        # Done
        self.after(500, self._on_downloads_done)

    def _download_vosk(self, lang: str, profile: str, key: str):
        """Download and extract a VOSK model."""
        vosk_urls = VOSK_MODEL_URLS.get(profile, VOSK_MODEL_URLS.get("cpu", {}))
        model_info = vosk_urls.get(lang)
        if not model_info:
            raise ValueError(f"No VOSK model URL for {lang}/{profile}")

        url = model_info["url"]
        dir_name = model_info["dir_name"]
        target_dir = MODELS_DIR / "vosk" / lang

        target_dir.mkdir(parents=True, exist_ok=True)
        zip_path = MODELS_DIR / f"{dir_name}.zip"

        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                pct = min(1.0, (block_num * block_size) / total_size)
                self._update_status(key, f"Downloading... {int(pct * 100)}%", pct * 0.7)

        urllib.request.urlretrieve(url, str(zip_path), reporthook=progress_hook)

        # Extract
        self._update_status(key, "Extracting...", 0.8)
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(str(MODELS_DIR))

        # Move to target
        extracted = MODELS_DIR / dir_name
        if extracted.exists() and extracted != target_dir:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            extracted.rename(target_dir)

        zip_path.unlink(missing_ok=True)
        self._update_status(key, "Done!", 1.0)

    def _pull_ollama_model(self, key: str):
        """Pull the Ollama LLM model."""
        import requests
        ollama_cfg = self._config.brain.get("ollama", {})
        model_name = ollama_cfg.get("model", "qwen2.5:1.5b")
        base_url = ollama_cfg.get("base_url", "http://localhost:11434")

        # Use streaming pull to track progress
        resp = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name, "stream": True},
            stream=True, timeout=600,
        )
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue
            import json
            data = json.loads(line)
            status = data.get("status", "")
            if "pulling" in status and "total" in data:
                total = data.get("total", 1)
                completed = data.get("completed", 0)
                pct = completed / total if total > 0 else 0
                self._update_status(key, f"{status}... {int(pct * 100)}%", pct)
            elif status == "success":
                self._update_status(key, "Done!", 1.0)

    def _update_status(self, key: str, text: str, progress: float):
        """Update a progress widget (thread-safe via after())."""
        def update():
            try:
                if key in self._progress_widgets and self.winfo_exists():
                    widgets = self._progress_widgets[key]
                    widgets["status"].configure(text=text)
                    widgets["progress"].set(progress)
            except Exception:
                pass  # Widget was destroyed — safe to ignore
        try:
            self.after(0, update)
        except Exception:
            pass  # Window already gone

    def _check_ollama(self):
        """Re-check if Ollama is now running."""
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                del self._missing["ollama"]
                self.after(0, lambda: self._on_downloads_done())
        except Exception:
            pass

    def _on_downloads_done(self):
        """Called when all downloads are complete."""
        # Re-check setup
        remaining = check_setup(self._config)
        if not remaining:
            self.grab_release()
            self.destroy()
            if self._on_complete:
                self._on_complete()
        else:
            self._start_btn.configure(
                state="normal", text="Retry",
                fg_color=YELLOW, text_color="black",
            )
