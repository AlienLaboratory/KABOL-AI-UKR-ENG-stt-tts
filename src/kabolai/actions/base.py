"""Base types for action results."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ActionResult:
    """Result from executing an action."""
    success: bool
    message: str
    data: Optional[Any] = None
    speak_text_en: Optional[str] = None
    speak_text_uk: Optional[str] = None
