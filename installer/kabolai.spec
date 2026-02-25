# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for KA-BOL-AI.

Build with:
    cd installer
    pyinstaller kabolai.spec

Output: dist/KA-BOL-AI/KA-BOL-AI.exe
"""

import sys
from pathlib import Path

block_cipher = None
ROOT = Path("..").resolve()

a = Analysis(
    [str(ROOT / "src" / "kabolai" / "gui" / "app.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        # Config files
        (str(ROOT / "config"), "config"),
        # Note: models/ are NOT bundled — first-run wizard downloads them
    ],
    hiddenimports=[
        # Core
        "kabolai",
        "kabolai.core",
        "kabolai.core.config",
        "kabolai.core.constants",
        "kabolai.core.state",
        "kabolai.core.exceptions",
        "kabolai.core.logging",
        # Audio
        "kabolai.audio",
        "kabolai.audio.recorder",
        "kabolai.audio.player",
        # STT
        "kabolai.stt",
        "kabolai.stt.factory",
        "kabolai.stt.vosk_engine",
        # TTS
        "kabolai.tts",
        "kabolai.tts.factory",
        "kabolai.tts.pyttsx3_engine",
        "kabolai.tts.ukrainian_engine",
        # Brain
        "kabolai.brain",
        "kabolai.brain.factory",
        "kabolai.brain.ollama_brain",
        "kabolai.brain.models",
        "kabolai.brain.prompts",
        # Actions (all must be imported for registry)
        "kabolai.actions",
        "kabolai.actions.registry",
        "kabolai.actions.apps",
        "kabolai.actions.system",
        "kabolai.actions.web",
        "kabolai.actions.media",
        "kabolai.actions.conversation",
        # UI
        "kabolai.ui",
        "kabolai.ui.hotkeys",
        "kabolai.ui.tray",
        "kabolai.ui.icons",
        # GUI
        "kabolai.gui",
        "kabolai.gui.app",
        "kabolai.gui.theme",
        "kabolai.gui.widgets",
        "kabolai.gui.first_run",
        "kabolai.gui.settings",
        # CLI
        "kabolai.cli",
        "kabolai.cli.main",
        # Assistant
        "kabolai.assistant",
        # Libraries
        "customtkinter",
        "pyttsx3",
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",
        "vosk",
        "sounddevice",
        "soundfile",
        "pystray",
        "keyboard",
        "pydantic",
        "yaml",
        "click",
        "requests",
        "psutil",
        "numpy",
        "PIL",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "scipy",
        "pandas",
        "jupyter",
        "notebook",
        "IPython",
        "tkinter.test",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KA-BOL-AI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=str(ROOT / "assets" / "icon.ico"),  # Uncomment when icon exists
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KA-BOL-AI",
)
