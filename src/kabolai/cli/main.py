"""CLI entry point for KA-BOL-AI."""

import logging
import sys
import threading
import time

import click

from kabolai import __version__

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
def main():
    """KA-BOL-AI: Bilingual voice-controlled PC assistant."""
    pass


@main.command()
@click.option("--profile", "-p", default=None,
              type=click.Choice(["cpu", "gpu_light", "gpu_full"]),
              help="Hardware profile")
@click.option("--language", "-l", default=None,
              type=click.Choice(["en", "uk"]),
              help="Starting language")
@click.option("--config", "-c", default=None,
              help="Path to custom config YAML")
@click.option("--no-tray", is_flag=True, help="Disable system tray icon")
def run(profile, language, config, no_tray):
    """Start the voice assistant."""
    from kabolai.core.config import AppConfig
    from kabolai.core.logging import setup_logging

    # Load config
    try:
        app_config = AppConfig.load(config_path=config, profile=profile)
        if language:
            app_config.language = language
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    # Setup logging
    log_cfg = app_config.logging
    setup_logging(
        level=log_cfg.get("level", "INFO"),
        log_file=log_cfg.get("file", "kabolai.log"),
    )

    click.echo(f"KA-BOL-AI v{__version__}")
    click.echo(f"Profile: {app_config.profile}")
    click.echo(f"Language: {app_config.language}")
    click.echo(f"STT: {app_config.stt.get('engine', 'vosk')}")
    click.echo(f"LLM: {app_config.brain.get('ollama', {}).get('model', 'qwen2.5:1.5b')}")
    click.echo()

    # Initialize assistant
    from kabolai.assistant import Assistant

    try:
        assistant = Assistant(app_config)
    except Exception as e:
        logger.error(f"Failed to initialize assistant: {e}", exc_info=True)
        click.echo(f"Initialization error: {e}", err=True)
        sys.exit(1)

    # Check brain availability
    if not assistant.check_brain():
        click.echo(
            "WARNING: Ollama is not reachable or the model is not loaded.\n"
            "Make sure Ollama is running: ollama serve\n"
            f"And the model is pulled: ollama pull {app_config.brain.get('ollama', {}).get('model', 'qwen2.5:1.5b')}",
            err=True,
        )

    # Setup UI
    from kabolai.ui.hotkeys import HotkeyManager
    hotkey_mgr = HotkeyManager(app_config.hotkeys)

    tray = None
    if not no_tray:
        from kabolai.ui.tray import SystemTray
        tray = SystemTray(
            state=assistant.state,
            on_toggle=lambda: _toggle_active(assistant, tray),
            on_language=lambda: _toggle_language(assistant, tray),
            on_quit=lambda: _quit(assistant, hotkey_mgr, tray),
        )
        tray.run_in_background()

    # Bind hotkeys — using the new self-healing handle_voice()
    def on_push_to_talk():
        if not assistant.state.is_active:
            return
        # handle_voice() has its own pipeline lock — no need to check
        # is_listening/is_processing here. If already busy, it returns
        # immediately. If stuck, the watchdog auto-resets.
        threading.Thread(
            target=assistant.handle_voice, daemon=True
        ).start()

    hotkey_mgr.bind(
        on_push_to_talk=on_push_to_talk,
        on_toggle_active=lambda: _toggle_active(assistant, tray),
        on_toggle_language=lambda: _toggle_language(assistant, tray),
        on_quit=lambda: _quit(assistant, hotkey_mgr, tray),
    )

    click.echo("Ready! Hotkeys:")
    click.echo(f"  {app_config.hotkeys.push_to_talk} = Push to talk")
    click.echo(f"  {app_config.hotkeys.toggle_active} = Toggle on/off")
    click.echo(f"  {app_config.hotkeys.toggle_language} = Switch EN/UK")
    click.echo(f"  {app_config.hotkeys.quit} = Quit")
    click.echo()

    # Main loop
    try:
        while assistant.state.is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        _quit(assistant, hotkey_mgr, tray)


def _toggle_active(assistant, tray=None):
    new_state = assistant.state.toggle_active()
    status = "ACTIVE" if new_state else "INACTIVE"
    click.echo(f"[{status}]")
    if new_state:
        # Force-reset pipeline state when reactivating
        assistant.state.force_reset()
    if tray:
        tray.update_icon()


def _toggle_language(assistant, tray=None):
    new_lang = assistant.state.toggle_language()
    click.echo(f"[Language: {new_lang.upper()}]")
    if tray:
        tray.update_icon()


def _quit(assistant, hotkey_mgr, tray=None):
    click.echo("Shutting down...")
    hotkey_mgr.unbind_all()
    if tray:
        tray.stop()
    assistant.shutdown()


@main.command()
@click.option("--profile", "-p", default=None,
              type=click.Choice(["cpu", "gpu_light", "gpu_full"]),
              help="Hardware profile")
@click.option("--language", "-l", default=None,
              type=click.Choice(["en", "uk"]),
              help="Starting language")
def gui(profile, language):
    """Launch the GUI application."""
    from kabolai.gui.app import main as gui_main
    gui_main(profile=profile, language=language)


@main.command()
@click.option("--profile", "-p", default="cpu",
              type=click.Choice(["cpu", "gpu_light", "gpu_full"]),
              help="Hardware profile to download models for")
def setup(profile):
    """Download models and verify setup."""
    click.echo(f"Setting up KA-BOL-AI for profile: {profile}")

    # Check Ollama
    click.echo("\nChecking Ollama...")
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            click.echo(f"  Ollama is running. Models: {', '.join(models) or 'none'}")
        else:
            click.echo("  Ollama responded but with an error.")
    except Exception:
        click.echo("  Ollama is NOT running. Start it with: ollama serve")

    # Check audio devices
    click.echo("\nChecking audio devices...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        inputs = [d for d in devices if d["max_input_channels"] > 0]
        click.echo(f"  Found {len(inputs)} input device(s):")
        for d in inputs[:5]:
            click.echo(f"    - {d['name']}")
    except Exception as e:
        click.echo(f"  Audio error: {e}")

    click.echo(f"\nTo download VOSK models, run:")
    click.echo(f"  python scripts/download_models.py --profile {profile}")
    click.echo(f"\nTo pull Ollama model, run:")
    click.echo(f"  python scripts/setup_ollama.py --profile {profile}")


@main.command()
def test():
    """Quick test of all components."""
    click.echo("Testing KA-BOL-AI components...\n")

    # Test imports
    click.echo("1. Testing imports...")
    try:
        from kabolai.core.config import AppConfig
        from kabolai.core.state import AssistantState
        from kabolai.actions.registry import registry
        from kabolai.brain.models import BrainResponse
        click.echo("   OK: All core imports work")
    except ImportError as e:
        click.echo(f"   FAIL: {e}")

    # Test action registry
    click.echo("\n2. Testing action registry...")
    import kabolai.actions.apps  # noqa
    import kabolai.actions.system  # noqa
    import kabolai.actions.web  # noqa
    import kabolai.actions.media  # noqa
    import kabolai.actions.conversation  # noqa
    actions = registry.list_actions()
    click.echo(f"   OK: {len(actions)} actions registered")
    for a in actions:
        click.echo(f"     - {a.name} ({a.category})")

    # Test audio
    click.echo("\n3. Testing audio...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        click.echo(f"   OK: sounddevice works ({len(devices)} devices)")
    except Exception as e:
        click.echo(f"   FAIL: {e}")

    # Test Ollama
    click.echo("\n4. Testing Ollama connection...")
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        click.echo(f"   OK: Ollama running, models: {', '.join(models) or 'none'}")
    except Exception:
        click.echo("   WARN: Ollama not reachable")

    click.echo("\nDone!")


if __name__ == "__main__":
    main()
