"""Setup Ollama and pull the correct model for the selected profile."""

import argparse
import subprocess
import sys

import requests

PROFILE_MODELS = {
    "cpu": "qwen2.5:1.5b",
    "gpu_light": "mistral:7b-q4_0",
    "gpu_full": "llama3:8b",
}


def check_ollama():
    """Check if Ollama is running."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def list_models():
    """List available Ollama models."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def pull_model(model_name: str):
    """Pull an Ollama model."""
    print(f"Pulling model: {model_name}")
    print("This may take a while depending on model size and internet speed...\n")

    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            check=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: 'ollama' command not found. Install Ollama first:")
        print("  https://ollama.com/download")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error pulling model: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup Ollama for KA-BOL-AI")
    parser.add_argument(
        "--profile", "-p",
        choices=["cpu", "gpu_light", "gpu_full"],
        default="cpu",
        help="Hardware profile (default: cpu)",
    )
    args = parser.parse_args()

    model = PROFILE_MODELS[args.profile]
    print(f"KA-BOL-AI Ollama Setup — Profile: {args.profile}")
    print(f"Required model: {model}\n")

    # Check Ollama
    if not check_ollama():
        print("Ollama is not running!")
        print("Start it with: ollama serve")
        print("Or install from: https://ollama.com/download")
        sys.exit(1)

    print("Ollama is running.")
    existing = list_models()
    print(f"Installed models: {', '.join(existing) or 'none'}\n")

    # Check if model already exists
    if any(model in m for m in existing):
        print(f"Model '{model}' is already installed!")
        return

    # Pull model
    if pull_model(model):
        print(f"\nModel '{model}' is ready!")
        print(f"Run the assistant with: kabolai run --profile {args.profile}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
