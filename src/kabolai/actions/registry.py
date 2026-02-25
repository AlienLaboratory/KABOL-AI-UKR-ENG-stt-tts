"""Decorator-based action registry for PC control commands."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from kabolai.actions.base import ActionResult

logger = logging.getLogger(__name__)


@dataclass
class ActionMeta:
    """Metadata for a registered action."""
    name: str
    category: str
    description_en: str
    description_uk: str
    parameters: list[dict] = field(default_factory=list)
    handler: Callable = field(default=None)
    aliases: list[str] = field(default_factory=list)


class ActionRegistry:
    """Singleton registry of all available actions."""

    _instance: Optional[ActionRegistry] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions = {}
        return cls._instance

    def register(
        self,
        name: str,
        category: str,
        description_en: str,
        description_uk: str,
        parameters: Optional[list[dict]] = None,
        aliases: Optional[list[str]] = None,
    ):
        """Decorator to register an action function."""
        def decorator(func: Callable) -> Callable:
            meta = ActionMeta(
                name=name,
                category=category,
                description_en=description_en,
                description_uk=description_uk,
                parameters=parameters or [],
                handler=func,
                aliases=aliases or [],
            )
            self._actions[name] = meta
            for alias in meta.aliases:
                self._actions[alias] = meta
            return func
        return decorator

    def get(self, name: str) -> Optional[ActionMeta]:
        return self._actions.get(name)

    def execute(self, name: str, params: dict) -> ActionResult:
        """Execute a registered action by name."""
        meta = self._actions.get(name)
        if meta is None:
            return ActionResult(
                success=False,
                message=f"Unknown action: {name}",
                speak_text_en=f"I don't know how to do that.",
                speak_text_uk=f"Я не знаю, як це зробити.",
            )
        try:
            return meta.handler(**params)
        except TypeError as e:
            logger.error(f"Action '{name}' parameter error: {e}")
            return ActionResult(
                success=False,
                message=f"Wrong parameters for {name}: {e}",
                speak_text_en=f"I had trouble with the parameters for that command.",
                speak_text_uk=f"У мене виникли проблеми з параметрами цієї команди.",
            )
        except Exception as e:
            logger.error(f"Action '{name}' failed: {e}", exc_info=True)
            return ActionResult(
                success=False,
                message=f"Action {name} failed: {e}",
                speak_text_en=f"Sorry, that command failed.",
                speak_text_uk=f"Вибачте, команда не виконалась.",
            )

    def list_actions(self, category: Optional[str] = None) -> list[ActionMeta]:
        """List unique actions, optionally filtered by category."""
        seen = set()
        result = []
        for meta in self._actions.values():
            if meta.name not in seen:
                if category is None or meta.category == category:
                    result.append(meta)
                    seen.add(meta.name)
        return result

    def get_schema_for_llm(self, language: str = "en") -> str:
        """Generate action schema text for the LLM system prompt."""
        lines = []
        for meta in self.list_actions():
            desc = meta.description_en if language == "en" else meta.description_uk
            params_parts = []
            for p in meta.parameters:
                req = " (required)" if p.get("required") else ""
                params_parts.append(f"{p['name']}: {p['type']}{req}")
            params_str = ", ".join(params_parts)
            lines.append(f"- {meta.name}({params_str}): {desc}")
        return "\n".join(lines)


# Module-level singleton
registry = ActionRegistry()
