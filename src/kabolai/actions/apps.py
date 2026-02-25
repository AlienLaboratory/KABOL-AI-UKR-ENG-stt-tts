"""Application management actions."""

import logging
import subprocess

import psutil

from kabolai.actions.base import ActionResult
from kabolai.actions.registry import registry

logger = logging.getLogger(__name__)

# App name -> executable mapping (English + Ukrainian aliases)
APP_MAP = {
    # English
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "terminal": "wt.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "task manager": "taskmgr.exe",
    "paint": "mspaint.exe",
    "snipping tool": "snippingtool.exe",
    "settings": "ms-settings:",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "code": "code",
    "vscode": "code",
    # Ukrainian
    "блокнот": "notepad.exe",
    "калькулятор": "calc.exe",
    "провідник": "explorer.exe",
    "термінал": "wt.exe",
    "диспетчер завдань": "taskmgr.exe",
    "налаштування": "ms-settings:",
    "браузер": "msedge.exe",
}


@registry.register(
    name="open_app",
    category="apps",
    description_en="Open an application by name",
    description_uk="Відкрити програму за назвою",
    parameters=[
        {"name": "app_name", "type": "str", "required": True,
         "description": "Name of the application to open"}
    ],
    aliases=["launch_app", "start_app"],
)
def open_app(app_name: str) -> ActionResult:
    """Open an application on Windows."""
    exe = APP_MAP.get(app_name.lower())
    target = exe or app_name

    try:
        if target.startswith("ms-"):
            # Windows URI scheme (settings, store, etc.)
            subprocess.Popen(["start", target], shell=True)
        else:
            subprocess.Popen(target, shell=True)
        return ActionResult(
            success=True,
            message=f"Opened {app_name}",
            speak_text_en=f"Opening {app_name}",
            speak_text_uk=f"Відкриваю {app_name}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Could not open {app_name}: {e}",
            speak_text_en=f"Sorry, I could not open {app_name}",
            speak_text_uk=f"Вибачте, не можу відкрити {app_name}",
        )


@registry.register(
    name="close_app",
    category="apps",
    description_en="Close an application by name",
    description_uk="Закрити програму за назвою",
    parameters=[
        {"name": "app_name", "type": "str", "required": True,
         "description": "Name of the application to close"}
    ],
)
def close_app(app_name: str) -> ActionResult:
    """Close an application by name."""
    app_lower = app_name.lower()
    killed = []

    for proc in psutil.process_iter(["name", "pid"]):
        try:
            proc_name = proc.info["name"].lower()
            if app_lower in proc_name:
                proc.terminate()
                killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return ActionResult(
            success=True,
            message=f"Closed: {', '.join(killed)}",
            speak_text_en=f"Closed {app_name}",
            speak_text_uk=f"Закрив {app_name}",
        )
    return ActionResult(
        success=False,
        message=f"No running process found for {app_name}",
        speak_text_en=f"I could not find {app_name} running",
        speak_text_uk=f"Не знайшов запущену програму {app_name}",
    )


@registry.register(
    name="list_running_apps",
    category="apps",
    description_en="List currently running applications",
    description_uk="Показати запущені програми",
)
def list_running_apps() -> ActionResult:
    """List visible running applications."""
    apps = set()
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"]
            if name and not name.startswith("svchost") and name.endswith(".exe"):
                apps.add(name.replace(".exe", ""))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_apps = sorted(apps)[:15]
    app_list = ", ".join(top_apps)

    return ActionResult(
        success=True,
        message=f"Running: {app_list}",
        data=top_apps,
        speak_text_en=f"You have {len(top_apps)} applications running, including {', '.join(top_apps[:5])}",
        speak_text_uk=f"У вас запущено {len(top_apps)} програм, зокрема {', '.join(top_apps[:5])}",
    )
