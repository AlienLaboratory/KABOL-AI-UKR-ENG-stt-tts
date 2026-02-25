"""System information and control actions."""

import datetime
import logging
import platform
import socket

import psutil

from kabolai.actions.base import ActionResult
from kabolai.actions.registry import registry

logger = logging.getLogger(__name__)


@registry.register(
    name="get_time",
    category="system",
    description_en="Get the current time",
    description_uk="Показати поточний час",
)
def get_time() -> ActionResult:
    """Report current time."""
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    time_en = now.strftime("%I:%M %p")

    return ActionResult(
        success=True,
        message=f"Current time: {time_str}",
        speak_text_en=f"The time is {time_en}",
        speak_text_uk=f"Зараз {time_str}",
    )


@registry.register(
    name="get_date",
    category="system",
    description_en="Get the current date",
    description_uk="Показати поточну дату",
)
def get_date() -> ActionResult:
    """Report current date."""
    now = datetime.datetime.now()
    date_en = now.strftime("%A, %B %d, %Y")
    date_uk = now.strftime("%d.%m.%Y")

    return ActionResult(
        success=True,
        message=f"Current date: {date_en}",
        speak_text_en=f"Today is {date_en}",
        speak_text_uk=f"Сьогодні {date_uk}",
    )


@registry.register(
    name="get_system_info",
    category="system",
    description_en="Get system information (CPU, RAM, disk, battery)",
    description_uk="Показати системну інформацію (процесор, пам'ять, диск, батарея)",
)
def get_system_info() -> ActionResult:
    """Report system status."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    info = {
        "cpu_percent": cpu_percent,
        "ram_used_gb": round(memory.used / (1024**3), 1),
        "ram_total_gb": round(memory.total / (1024**3), 1),
        "ram_percent": memory.percent,
        "disk_used_gb": round(disk.used / (1024**3), 1),
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_percent": disk.percent,
    }

    battery = psutil.sensors_battery()
    if battery:
        info["battery_percent"] = battery.percent
        info["battery_plugged"] = battery.power_plugged

    en_text = (
        f"CPU is at {cpu_percent}%, "
        f"RAM {memory.percent}% used ({info['ram_used_gb']} of {info['ram_total_gb']} GB), "
        f"disk {disk.percent}% used"
    )
    uk_text = (
        f"Процесор {cpu_percent}%, "
        f"пам'ять {memory.percent}% ({info['ram_used_gb']} з {info['ram_total_gb']} ГБ), "
        f"диск {disk.percent}%"
    )

    if battery:
        en_text += f", battery {battery.percent}%"
        uk_text += f", батарея {battery.percent}%"

    return ActionResult(
        success=True,
        message=en_text,
        data=info,
        speak_text_en=en_text,
        speak_text_uk=uk_text,
    )


@registry.register(
    name="get_ip_address",
    category="system",
    description_en="Get the local IP address",
    description_uk="Показати IP-адресу",
)
def get_ip_address() -> ActionResult:
    """Report local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "unknown"

    hostname = socket.gethostname()

    return ActionResult(
        success=True,
        message=f"IP: {local_ip}, hostname: {hostname}",
        data={"ip": local_ip, "hostname": hostname},
        speak_text_en=f"Your local IP address is {local_ip}",
        speak_text_uk=f"Ваша локальна IP-адреса {local_ip}",
    )
