"""Download VOSK models for the selected hardware profile."""

import argparse
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "models" / "vosk"

VOSK_MODELS = {
    "cpu": {
        "en": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "dir_name": "vosk-model-small-en-us-0.15",
            "size_mb": 40,
        },
        "uk": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-uk-v3-nano.zip",
            "dir_name": "vosk-model-small-uk-v3-nano",
            "size_mb": 73,
        },
    },
    "gpu_light": {
        "en": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip",
            "dir_name": "vosk-model-en-us-0.22-lgraph",
            "size_mb": 128,
        },
        "uk": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-uk-v3-small.zip",
            "dir_name": "vosk-model-uk-v3-small",
            "size_mb": 133,
        },
    },
    "gpu_full": {
        "en": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip",
            "dir_name": "vosk-model-en-us-0.22-lgraph",
            "size_mb": 128,
        },
        "uk": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-uk-v3-small.zip",
            "dir_name": "vosk-model-uk-v3-small",
            "size_mb": 133,
        },
    },
}


def download_model(url: str, target_dir: Path, dir_name: str, size_mb: int):
    """Download and extract a VOSK model."""
    target_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if any(target_dir.iterdir()):
        print(f"  Model already exists at {target_dir}, skipping.")
        return

    zip_path = target_dir.parent / f"{dir_name}.zip"

    print(f"  Downloading {url} (~{size_mb}MB)...")
    try:
        urllib.request.urlretrieve(url, str(zip_path), reporthook=_progress)
        print()
    except Exception as e:
        print(f"\n  Download failed: {e}")
        return

    print(f"  Extracting to {target_dir}...")
    try:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(str(target_dir.parent))

        # Move contents from extracted dir to target
        extracted = target_dir.parent / dir_name
        if extracted.exists() and extracted != target_dir:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            extracted.rename(target_dir)

        zip_path.unlink(missing_ok=True)
        print(f"  Done!")
    except Exception as e:
        print(f"  Extraction failed: {e}")
        zip_path.unlink(missing_ok=True)


def _progress(block_num, block_size, total_size):
    """Download progress callback."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 // total_size)
        bar = "#" * (percent // 5) + "-" * (20 - percent // 5)
        print(f"\r  [{bar}] {percent}%", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Download VOSK models")
    parser.add_argument(
        "--profile", "-p",
        choices=["cpu", "gpu_light", "gpu_full"],
        default="cpu",
        help="Hardware profile (default: cpu)",
    )
    args = parser.parse_args()

    models = VOSK_MODELS[args.profile]
    print(f"Downloading VOSK models for profile: {args.profile}\n")

    for lang, info in models.items():
        target = MODELS_DIR / lang
        print(f"[{lang.upper()}] {info['dir_name']} (~{info['size_mb']}MB)")
        download_model(info["url"], target, info["dir_name"], info["size_mb"])
        print()

    print("All models downloaded. You can now run: kabolai run")


if __name__ == "__main__":
    main()
