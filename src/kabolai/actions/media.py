"""Media and volume control actions (Windows)."""

import ctypes
import logging

from kabolai.actions.base import ActionResult
from kabolai.actions.registry import registry

logger = logging.getLogger(__name__)

# Windows virtual key codes for volume control
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_KEYUP = 0x0002


def _press_volume_key(vk_code: int, times: int = 1):
    """Send volume key presses via Windows API."""
    user32 = ctypes.windll.user32
    for _ in range(times):
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


@registry.register(
    name="volume_up",
    category="media",
    description_en="Increase system volume",
    description_uk="Збільшити гучність",
    parameters=[
        {"name": "amount", "type": "int", "required": False,
         "description": "Number of volume steps (default 5)"}
    ],
)
def volume_up(amount: int = 5) -> ActionResult:
    """Increase system volume."""
    try:
        _press_volume_key(VK_VOLUME_UP, times=amount)
        return ActionResult(
            success=True,
            message=f"Volume up by {amount} steps",
            speak_text_en="Volume up",
            speak_text_uk="Гучність збільшено",
        )
    except Exception as e:
        return ActionResult(success=False, message=f"Volume control failed: {e}")


@registry.register(
    name="volume_down",
    category="media",
    description_en="Decrease system volume",
    description_uk="Зменшити гучність",
    parameters=[
        {"name": "amount", "type": "int", "required": False,
         "description": "Number of volume steps (default 5)"}
    ],
)
def volume_down(amount: int = 5) -> ActionResult:
    """Decrease system volume."""
    try:
        _press_volume_key(VK_VOLUME_DOWN, times=amount)
        return ActionResult(
            success=True,
            message=f"Volume down by {amount} steps",
            speak_text_en="Volume down",
            speak_text_uk="Гучність зменшено",
        )
    except Exception as e:
        return ActionResult(success=False, message=f"Volume control failed: {e}")


@registry.register(
    name="volume_mute",
    category="media",
    description_en="Toggle mute/unmute",
    description_uk="Вимкнути/увімкнути звук",
)
def volume_mute() -> ActionResult:
    """Toggle mute."""
    try:
        _press_volume_key(VK_VOLUME_MUTE, times=1)
        return ActionResult(
            success=True,
            message="Toggled mute",
            speak_text_en="Toggled mute",
            speak_text_uk="Звук перемикнуто",
        )
    except Exception as e:
        return ActionResult(success=False, message=f"Mute toggle failed: {e}")
