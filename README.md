# KA-BOL-AI-UKR-ENG

**Bilingual Voice-Controlled PC Assistant — English + Ukrainian**

A Jarvis-like voice assistant that runs 100% locally and free. Speak commands in English or Ukrainian to control your PC — open apps, search the web, manage volume, get system info, and more. No cloud APIs, no subscriptions, no data leaving your machine.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-Windows-blue.svg" alt="Windows">
  <img src="https://img.shields.io/badge/languages-EN%20%2B%20UK-yellow.svg" alt="EN + UK">
  <img src="https://img.shields.io/badge/100%25-local%20%26%20free-brightgreen.svg" alt="Local & Free">
</p>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Hardware Profiles](#hardware-profiles)
- [Installation](#installation)
  - [Option A: pip + venv (Recommended)](#option-a-pip--venv-recommended)
  - [Option B: Conda / Miniconda](#option-b-conda--miniconda)
  - [Option C: Docker (Coming Soon)](#option-c-docker-coming-soon)
- [Setup Models](#setup-models)
  - [Step 1: Download VOSK Speech Models](#step-1-download-vosk-speech-models)
  - [Step 2: Install & Configure Ollama](#step-2-install--configure-ollama)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Hotkeys](#hotkeys)
  - [CLI Commands](#cli-commands)
  - [Voice Commands](#voice-commands)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

---

## Features

| Feature | Details |
|---------|---------|
| **Bilingual** | English + Ukrainian with runtime language switching |
| **100% Local** | All models run on your machine — no internet needed at runtime |
| **100% Free** | All open-source components, no paid APIs |
| **Scalable** | 3 hardware profiles: CPU-only, GPU 4-6GB, GPU 8GB+ |
| **15 Voice Commands** | Apps, system, web, media, and meta commands |
| **System Tray** | Clean UI with on/off toggle and status indicator |
| **Push-to-Talk** | Hotkey-activated — no false triggers, no always-listening |
| **Configurable** | YAML-based config, customizable hotkeys, voices, and models |

---

## Architecture

```
                    +-----------+
                    | Microphone|
                    +-----+-----+
                          |
               Ctrl+Shift+Space (push-to-talk)
                          |
                    +-----v-----+
                    |  VOSK STT  |  (or faster-whisper on GPU)
                    +-----+-----+
                          |
                     text string
                          |
                    +-----v-----+
                    |  Ollama    |  Local LLM parses intent
                    |  Brain     |  -> structured JSON command
                    +-----+-----+
                          |
                   {action, params}
                          |
                    +-----v-----+
                    |  Action    |  Execute: open app, search,
                    |  Registry  |  volume, system info, etc.
                    +-----+-----+
                          |
                    response text
                          |
                    +-----v-----+
                    |  TTS       |  pyttsx3 (EN) or
                    |  Engine    |  ukrainian-tts (UK)
                    +-----+-----+
                          |
                    +-----v-----+
                    |  Speaker   |
                    +-----------+
```

**Tech Stack:**

| Layer | Component | License |
|-------|-----------|---------|
| Speech-to-Text | [VOSK](https://alphacephei.com/vosk/) / [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Apache 2.0 |
| Text-to-Speech (EN) | [pyttsx3](https://github.com/nateshmbhat/pyttsx3) / [piper-tts](https://github.com/rhasspy/piper) | MIT |
| Text-to-Speech (UK) | [ukrainian-tts](https://github.com/robinhad/ukrainian-tts) | MIT |
| LLM Brain | [Ollama](https://ollama.com/) + Qwen/Mistral/Llama | MIT / Apache 2.0 |
| Audio | [sounddevice](https://github.com/spatialaudio/python-sounddevice) | MIT |
| UI | [pystray](https://github.com/moses-palmer/pystray) + [keyboard](https://github.com/boppreh/keyboard) | LGPL / MIT |

---

## Hardware Profiles

Choose the profile that matches your hardware:

| Profile | STT | LLM Model | TTS (EN) | Min RAM | GPU VRAM |
|---------|-----|-----------|----------|---------|----------|
| **`cpu`** | VOSK small (~113MB) | qwen2.5:1.5b (~1GB) | pyttsx3 (SAPI5) | 4GB | None |
| **`gpu_light`** | VOSK medium (~261MB) | mistral:7b-q4_0 (~4GB) | piper-tts | 8GB | 4-6GB |
| **`gpu_full`** | faster-whisper small | llama3:8b (~5GB) | piper-tts | 16GB | 8GB+ |

---

## Installation

### Prerequisites

- **Python 3.9+** (3.9, 3.10, 3.11, or 3.12)
- **Windows 10/11** (Linux/macOS support planned)
- **Ollama** installed ([download here](https://ollama.com/download))
- **Microphone** connected
- **Git** (for cloning)

---

### Option A: pip + venv (Recommended)

The simplest approach. Works on any machine with Python installed.

```bash
# 1. Clone the repository
git clone https://github.com/AlienLaboratory/KABOL-AI-UKR-ENG-stt-tts.git
cd KABOL-AI-UKR-ENG-stt-tts

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
# Windows (Command Prompt):
.venv\Scripts\activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Git Bash / MSYS2):
source .venv/Scripts/activate

# 4. Install the package
pip install -e .

# 5. (GPU users only) Install GPU extras
pip install -e ".[gpu]"

# 6. Verify installation
kabolai test
```

---

### Option B: Conda / Miniconda

Best if you already use Conda or need fine-grained control over Python/CUDA versions.

```bash
# 1. Clone the repository
git clone https://github.com/AlienLaboratory/KABOL-AI-UKR-ENG-stt-tts.git
cd KABOL-AI-UKR-ENG-stt-tts

# 2. Create a conda environment
conda create -n kabolai python=3.11 -y
conda activate kabolai

# 3. (GPU users) Install PyTorch with CUDA via conda first
#    For CUDA 11.8:
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y
#    For CUDA 12.1:
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
#    For CPU only — skip this step, pip will install CPU torch automatically

# 4. Install system audio dependencies (conda-forge)
conda install -c conda-forge portaudio libsndfile -y

# 5. Install KA-BOL-AI
pip install -e .

# 6. (GPU users) Install GPU extras
pip install -e ".[gpu]"

# 7. Verify
kabolai test
```

**Conda + specific Python version:**

```bash
# If you need Python 3.9 specifically
conda create -n kabolai python=3.9 -y
conda activate kabolai
pip install -e .
```

**Conda with environment.yml** (alternative):

```bash
# Create environment from the repo
conda env create -f environment.yml
conda activate kabolai
pip install -e .
```

> **Note:** The `ukrainian-tts` package installs PyTorch as a dependency (~2GB). If you pre-install PyTorch via conda with CUDA support, the pip install will reuse it.

---

### Option C: Docker (Coming Soon)

Docker support is planned for future releases.

---

### Platform-Specific Notes

<details>
<summary><strong>Windows 10/11</strong></summary>

- Works out of the box.
- pyttsx3 uses Windows SAPI5 for English TTS — no extra setup needed.
- If you get `PortAudio` errors, install it manually:
  ```
  pip install sounddevice --force-reinstall
  ```

</details>

<details>
<summary><strong>Linux (Experimental)</strong></summary>

- Install PortAudio system-wide:
  ```bash
  sudo apt-get install portaudio19-dev python3-pyaudio libsndfile1
  ```
- pyttsx3 uses `espeak` on Linux:
  ```bash
  sudo apt-get install espeak
  ```
- Volume control uses different system calls — media actions may need adaptation.

</details>

<details>
<summary><strong>macOS (Experimental)</strong></summary>

- Install PortAudio via Homebrew:
  ```bash
  brew install portaudio libsndfile
  ```
- pyttsx3 uses `nsss` (macOS native) for English TTS.
- The `keyboard` library may require accessibility permissions.

</details>

---

## Setup Models

After installing the package, you need to download the speech and LLM models.

### Step 1: Download VOSK Speech Models

```bash
# For CPU profile (~113MB download):
python scripts/download_models.py --profile cpu

# For GPU light profile (~261MB download):
python scripts/download_models.py --profile gpu_light

# For GPU full profile (uses faster-whisper, models auto-download):
python scripts/download_models.py --profile gpu_full
```

This downloads language models to the `models/vosk/` directory:

| Profile | English Model | Ukrainian Model | Total Size |
|---------|---------------|-----------------|------------|
| cpu | vosk-model-small-en-us-0.15 (40MB) | vosk-model-small-uk-v3-nano (73MB) | ~113MB |
| gpu_light | vosk-model-en-us-0.22-lgraph (128MB) | vosk-model-uk-v3-small (133MB) | ~261MB |
| gpu_full | faster-whisper (auto-downloads) | faster-whisper (auto-downloads) | ~500MB |

### Step 2: Install & Configure Ollama

**Install Ollama** (if not already installed):

```bash
# Windows — download installer:
# https://ollama.com/download/windows

# Or via winget:
winget install Ollama.Ollama

# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# macOS:
brew install ollama
```

**Start the Ollama server:**

```bash
ollama serve
```

> Keep this terminal open. Ollama needs to be running whenever you use KA-BOL-AI.

**Pull the LLM model for your profile:**

```bash
# CPU profile (smallest, ~1GB):
ollama pull qwen2.5:1.5b

# GPU light profile (~4GB):
ollama pull mistral:7b-q4_0

# GPU full profile (~5GB):
ollama pull llama3:8b
```

Or use the setup script:

```bash
python scripts/setup_ollama.py --profile cpu
```

**Verify everything works:**

```bash
kabolai test
```

Expected output:
```
Testing KA-BOL-AI components...

1. Testing imports...
   OK: All core imports work

2. Testing action registry...
   OK: 15 actions registered

3. Testing audio...
   OK: sounddevice works (N devices)

4. Testing Ollama connection...
   OK: Ollama running, models: qwen2.5:1.5b:latest

Done!
```

---

## Usage

### Quick Start

```bash
# Make sure Ollama is running (in another terminal):
ollama serve

# Start the assistant:
kabolai run

# With a specific profile:
kabolai run --profile gpu_full

# Start in Ukrainian:
kabolai run --language uk

# Combine options:
kabolai run --profile gpu_light --language uk
```

### Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+Space` | **Push to talk** — press, speak your command, release |
| `Ctrl+Shift+A` | **Toggle on/off** — enable/disable the assistant |
| `Ctrl+Shift+L` | **Switch language** — toggle between English and Ukrainian |
| `Ctrl+Shift+Q` | **Quit** — shut down the assistant |

### CLI Commands

```bash
kabolai run       # Start the voice assistant
kabolai setup     # Check dependencies and show setup instructions
kabolai test      # Quick test of all components
kabolai --version # Show version
kabolai --help    # Show help
```

### Voice Commands

**Apps (3 commands):**

| Say (English) | Say (Ukrainian) | What it does |
|---------------|-----------------|-------------|
| "Open calculator" | "Відкрий калькулятор" | Opens the calculator app |
| "Close notepad" | "Закрий блокнот" | Closes notepad |
| "What apps are running?" | "Які програми запущені?" | Lists running applications |

**System (4 commands):**

| Say (English) | Say (Ukrainian) | What it does |
|---------------|-----------------|-------------|
| "What time is it?" | "Котра година?" | Reports current time |
| "What's today's date?" | "Яка сьогодні дата?" | Reports current date |
| "System info" | "Інформація про систему" | CPU, RAM, disk, battery |
| "What's my IP?" | "Яка моя IP адреса?" | Reports local IP address |

**Web (2 commands):**

| Say (English) | Say (Ukrainian) | What it does |
|---------------|-----------------|-------------|
| "Search for Python tutorials" | "Пошукай Python уроки" | Opens Google search |
| "Open github.com" | "Відкрий github.com" | Opens URL in browser |

**Media (3 commands):**

| Say (English) | Say (Ukrainian) | What it does |
|---------------|-----------------|-------------|
| "Turn up the volume" | "Збільш гучність" | Volume up |
| "Turn down the volume" | "Зменш гучність" | Volume down |
| "Mute" | "Вимкни звук" | Toggle mute |

**Meta (3 commands):**

| Say (English) | Say (Ukrainian) | What it does |
|---------------|-----------------|-------------|
| "Switch to Ukrainian" | "Переключи на англійську" | Changes language |
| "List commands" | "Покажи команди" | Lists available commands |
| "Shut down" | "Вимкнися" | Stops the assistant |

---

## Configuration

Configuration lives in `config/default.yaml`. Override with profile-specific files in `config/profiles/`.

**Key settings:**

```yaml
# Hardware profile
profile: "cpu"          # "cpu", "gpu_light", "gpu_full"

# Starting language
language: "en"          # "en" or "uk"

# Hotkey bindings (customize these!)
hotkeys:
  push_to_talk: "ctrl+shift+space"
  toggle_active: "ctrl+shift+a"
  toggle_language: "ctrl+shift+l"
  quit: "ctrl+shift+q"

# Audio settings
audio:
  silence_threshold: 500    # Lower = more sensitive
  silence_duration: 1.5     # Seconds of silence to stop recording
  max_record_seconds: 30    # Maximum recording length

# LLM model (change per profile)
brain:
  ollama:
    model: "qwen2.5:1.5b"  # or "mistral:7b-q4_0" or "llama3:8b"

# Ukrainian TTS voice
tts:
  ukrainian:
    voice: "Dmytro"         # Oleksa, Tetiana, Dmytro, Lada, Mykyta
```

**Custom config file:**

```bash
kabolai run --config my_config.yaml
```

---

## Troubleshooting

<details>
<summary><strong>"Ollama not reachable"</strong></summary>

Make sure Ollama is running:
```bash
ollama serve
```
Then verify the model is pulled:
```bash
ollama list
# Should show your model, e.g. qwen2.5:1.5b:latest
```

</details>

<details>
<summary><strong>"VOSK model not found"</strong></summary>

Download models for your profile:
```bash
python scripts/download_models.py --profile cpu
```
Check that `models/vosk/en/` and `models/vosk/uk/` directories contain model files.

</details>

<details>
<summary><strong>"No audio devices found"</strong></summary>

- Check that your microphone is connected and enabled in Windows Sound Settings.
- Try: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- On Windows, make sure the correct default input device is set.

</details>

<details>
<summary><strong>"pyttsx3 init failed"</strong></summary>

- On Windows, pyttsx3 uses SAPI5. Make sure Windows Speech is enabled.
- Try: `pip install pyttsx3 --force-reinstall`
- Alternative: Install a specific SAPI5 voice pack in Windows Settings > Speech.

</details>

<details>
<summary><strong>"keyboard library requires root" (Linux)</strong></summary>

The `keyboard` library requires root on Linux. Either:
- Run with `sudo`: `sudo kabolai run`
- Or use an alternative input method (planned for future releases).

</details>

<details>
<summary><strong>Slow response / high latency</strong></summary>

- **CPU profile is slow?** The qwen2.5:1.5b model needs ~2-3s per response on CPU. This is normal.
- **GPU users:** Make sure Ollama is using your GPU: `ollama run qwen2.5:1.5b "test"` should be fast.
- Lower the STT model size or switch to a lighter LLM.
- Check `logs/kabolai.log` for timing info.

</details>

<details>
<summary><strong>Ukrainian TTS first-time slow startup</strong></summary>

The `ukrainian-tts` ESPnet model downloads on first use (~500MB). This is a one-time download. After that, it loads from cache in 2-3 seconds.

</details>

---

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/AlienLaboratory/KABOL-AI-UKR-ENG-stt-tts.git
cd KABOL-AI-UKR-ENG-stt-tts
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"

# Run tests (53 tests)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=kabolai --cov-report=term-missing

# Project structure
src/kabolai/
  core/       # Config, state, logging, constants
  audio/      # Mic recording + playback
  stt/        # Speech-to-text engines (VOSK, faster-whisper)
  tts/        # Text-to-speech (pyttsx3, piper, ukrainian-tts)
  brain/      # Ollama LLM integration + prompt engineering
  actions/    # Registry + 15 PC control commands
  ui/         # System tray + global hotkeys
  cli/        # Click-based CLI entry point
```

**Adding a new voice command** is easy:

```python
# In src/kabolai/actions/your_module.py
from kabolai.actions.registry import registry
from kabolai.actions.base import ActionResult

@registry.register(
    name="my_command",
    category="custom",
    description_en="Does something cool",
    description_uk="Робить щось круте",
    parameters=[{"name": "arg1", "type": "str", "required": True}],
)
def my_command(arg1: str) -> ActionResult:
    # Your logic here
    return ActionResult(
        success=True,
        message=f"Did something with {arg1}",
        speak_text_en=f"Done with {arg1}",
        speak_text_uk=f"Готово з {arg1}",
    )
```

The LLM brain automatically discovers new commands via the registry — no prompt changes needed.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

All third-party models and libraries have their own licenses (Apache 2.0, MIT, LGPL). Check individual components before commercial use.

---

---

# KA-BOL-AI-UKR-ENG

**Двомовний голосовий помічник для ПК — Англійська + Українська**

Голосовий помічник типу Jarvis, який працює 100% локально і безкоштовно. Говоріть команди англійською або українською, щоб керувати ПК — відкривати програми, шукати в інтернеті, керувати гучністю, отримувати інформацію про систему тощо. Без хмарних API, без підписок, дані не залишають вашу машину.

---

## Зміст

- [Можливості](#можливості)
- [Профілі обладнання](#профілі-обладнання)
- [Встановлення](#встановлення)
  - [Варіант А: pip + venv](#варіант-а-pip--venv)
  - [Варіант Б: Conda / Miniconda](#варіант-б-conda--miniconda)
- [Налаштування моделей](#налаштування-моделей)
  - [Крок 1: Завантажити VOSK моделі](#крок-1-завантажити-vosk-моделі)
  - [Крок 2: Встановити Ollama та LLM](#крок-2-встановити-ollama-та-llm)
- [Використання](#використання)
  - [Швидкий старт](#швидкий-старт)
  - [Гарячі клавіші](#гарячі-клавіші)
  - [Голосові команди](#голосові-команди)
- [Конфігурація](#конфігурація)
- [Вирішення проблем](#вирішення-проблем)

---

## Можливості

| Можливість | Деталі |
|------------|--------|
| **Двомовність** | Англійська + Українська з перемиканням у реальному часі |
| **100% Локально** | Всі моделі працюють на вашому ПК — інтернет не потрібен |
| **100% Безкоштовно** | Всі компоненти з відкритим кодом |
| **Масштабованість** | 3 профілі: тільки CPU, GPU 4-6GB, GPU 8GB+ |
| **15 голосових команд** | Програми, система, веб, медіа, мета-команди |
| **Системний трей** | Іконка з індикатором стану та перемикачем |
| **Push-to-talk** | Активація гарячою клавішею — без хибних спрацювань |

---

## Профілі обладнання

| Профіль | STT | LLM модель | TTS (EN) | Мін. RAM | GPU VRAM |
|---------|-----|------------|----------|----------|----------|
| **`cpu`** | VOSK small (~113MB) | qwen2.5:1.5b (~1GB) | pyttsx3 | 4GB | Не потрібно |
| **`gpu_light`** | VOSK medium (~261MB) | mistral:7b-q4_0 (~4GB) | piper-tts | 8GB | 4-6GB |
| **`gpu_full`** | faster-whisper | llama3:8b (~5GB) | piper-tts | 16GB | 8GB+ |

---

## Встановлення

### Передумови

- **Python 3.9+**
- **Windows 10/11**
- **Ollama** ([завантажити тут](https://ollama.com/download))
- **Мікрофон**
- **Git**

### Варіант А: pip + venv

```bash
# 1. Клонувати репозиторій
git clone https://github.com/AlienLaboratory/KABOL-AI-UKR-ENG-stt-tts.git
cd KABOL-AI-UKR-ENG-stt-tts

# 2. Створити віртуальне середовище
python -m venv .venv

# 3. Активувати його
# Windows (CMD):
.venv\Scripts\activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Git Bash):
source .venv/Scripts/activate

# 4. Встановити пакет
pip install -e .

# 5. (Тільки для GPU) Встановити GPU додатки
pip install -e ".[gpu]"

# 6. Перевірити встановлення
kabolai test
```

### Варіант Б: Conda / Miniconda

```bash
# 1. Клонувати репозиторій
git clone https://github.com/AlienLaboratory/KABOL-AI-UKR-ENG-stt-tts.git
cd KABOL-AI-UKR-ENG-stt-tts

# 2. Створити conda середовище
conda create -n kabolai python=3.11 -y
conda activate kabolai

# 3. (Для GPU) Встановити PyTorch з CUDA через conda
#    Для CUDA 11.8:
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y
#    Для CUDA 12.1:
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y

# 4. Встановити аудіо залежності
conda install -c conda-forge portaudio libsndfile -y

# 5. Встановити KA-BOL-AI
pip install -e .

# 6. (Для GPU) Додаткові пакети
pip install -e ".[gpu]"

# 7. Перевірити
kabolai test
```

---

## Налаштування моделей

### Крок 1: Завантажити VOSK моделі

```bash
# Для CPU профілю (~113MB):
python scripts/download_models.py --profile cpu

# Для GPU light (~261MB):
python scripts/download_models.py --profile gpu_light

# Для GPU full (faster-whisper завантажиться автоматично):
python scripts/download_models.py --profile gpu_full
```

### Крок 2: Встановити Ollama та LLM

**Встановити Ollama:**

```bash
# Windows:
winget install Ollama.Ollama
# Або завантажити з: https://ollama.com/download
```

**Запустити сервер Ollama** (в окремому терміналі):

```bash
ollama serve
```

**Завантажити модель:**

```bash
# CPU (~1GB):
ollama pull qwen2.5:1.5b

# GPU light (~4GB):
ollama pull mistral:7b-q4_0

# GPU full (~5GB):
ollama pull llama3:8b
```

**Перевірити:**

```bash
kabolai test
```

---

## Використання

### Швидкий старт

```bash
# Переконайтеся, що Ollama запущений:
ollama serve

# Запустити помічника:
kabolai run

# З конкретним профілем:
kabolai run --profile gpu_full

# Почати українською:
kabolai run --language uk
```

### Гарячі клавіші

| Клавіші | Дія |
|---------|-----|
| `Ctrl+Shift+Space` | **Натисніть і говоріть** — запис голосу |
| `Ctrl+Shift+A` | **Увімк/Вимк** — активувати/деактивувати помічника |
| `Ctrl+Shift+L` | **Змінити мову** — перемикання EN/UK |
| `Ctrl+Shift+Q` | **Вихід** — вимкнути помічника |

### Голосові команди

**Програми:**

| Скажіть | Що зробить |
|---------|-----------|
| "Відкрий калькулятор" | Відкриває калькулятор |
| "Закрий блокнот" | Закриває блокнот |
| "Які програми запущені?" | Показує список програм |

**Система:**

| Скажіть | Що зробить |
|---------|-----------|
| "Котра година?" | Повідомляє час |
| "Яка сьогодні дата?" | Повідомляє дату |
| "Інформація про систему" | CPU, RAM, диск, батарея |
| "Яка моя IP адреса?" | Показує IP адресу |

**Веб:**

| Скажіть | Що зробить |
|---------|-----------|
| "Пошукай Python уроки" | Відкриває пошук Google |
| "Відкрий github.com" | Відкриває URL в браузері |

**Медіа:**

| Скажіть | Що зробить |
|---------|-----------|
| "Збільш гучність" | Гучність вгору |
| "Зменш гучність" | Гучність вниз |
| "Вимкни звук" | Вимкнути/увімкнути звук |

**Мета-команди:**

| Скажіть | Що зробить |
|---------|-----------|
| "Переключи на англійську" | Змінює мову |
| "Покажи команди" | Список доступних команд |
| "Вимкнися" | Вимикає помічника |

---

## Конфігурація

Конфігурація знаходиться в `config/default.yaml`.

Основні налаштування:

```yaml
profile: "cpu"          # "cpu", "gpu_light", "gpu_full"
language: "en"          # "en" або "uk"

hotkeys:
  push_to_talk: "ctrl+shift+space"
  toggle_language: "ctrl+shift+l"

tts:
  ukrainian:
    voice: "Dmytro"     # Oleksa, Tetiana, Dmytro, Lada, Mykyta
```

---

## Вирішення проблем

| Проблема | Рішення |
|----------|---------|
| "Ollama not reachable" | Запустіть `ollama serve` та `ollama pull qwen2.5:1.5b` |
| "VOSK model not found" | Запустіть `python scripts/download_models.py --profile cpu` |
| "No audio devices" | Перевірте мікрофон у налаштуваннях Windows |
| Повільна відповідь | Нормально для CPU (~2-3с). GPU профіль швидший |
| Довгий перший запуск TTS | Модель українського TTS завантажується один раз (~500MB) |

---

## Ліцензія

MIT License. Дивіться [LICENSE](LICENSE).

---

<p align="center">
  Built with care at <a href="https://github.com/AlienLaboratory">AlienLaboratory</a>
</p>
