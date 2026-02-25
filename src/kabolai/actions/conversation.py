"""Meta-commands: language switch, help, exit."""

import logging

from kabolai.actions.base import ActionResult
from kabolai.actions.registry import registry

logger = logging.getLogger(__name__)

# These actions need access to the assistant state, which is injected at runtime
_state_ref = None


def set_state_ref(state):
    """Set the assistant state reference for meta-commands."""
    global _state_ref
    _state_ref = state


@registry.register(
    name="switch_language",
    category="conversation",
    description_en="Switch language between English and Ukrainian",
    description_uk="Перемикнути мову між англійською та українською",
    parameters=[
        {"name": "language", "type": "str", "required": False,
         "description": "Target language: 'en' or 'uk'. If omitted, toggles."}
    ],
)
def switch_language(language: str = None) -> ActionResult:
    """Switch the assistant language."""
    if _state_ref is None:
        return ActionResult(success=False, message="State not available")

    if language:
        new_lang = _state_ref.set_language(language)
    else:
        new_lang = _state_ref.toggle_language()

    if new_lang == "uk":
        return ActionResult(
            success=True,
            message=f"Language switched to Ukrainian",
            speak_text_en="Switching to Ukrainian",
            speak_text_uk="Перемикаюсь на українську",
        )
    else:
        return ActionResult(
            success=True,
            message=f"Language switched to English",
            speak_text_en="Switching to English",
            speak_text_uk="Switching to English",
        )


@registry.register(
    name="list_commands",
    category="conversation",
    description_en="List all available voice commands",
    description_uk="Показати всі доступні голосові команди",
)
def list_commands() -> ActionResult:
    """List available commands."""
    actions = registry.list_actions()
    by_category = {}
    for a in actions:
        by_category.setdefault(a.category, []).append(a.name)

    lines_en = []
    lines_uk = []
    for cat, names in by_category.items():
        lines_en.append(f"{cat}: {', '.join(names)}")
        lines_uk.append(f"{cat}: {', '.join(names)}")

    summary_en = f"I have {len(actions)} commands available. " + ". ".join(lines_en)
    summary_uk = f"У мене є {len(actions)} команд. " + ". ".join(lines_uk)

    return ActionResult(
        success=True,
        message=summary_en,
        data=by_category,
        speak_text_en=f"I have {len(actions)} commands across {len(by_category)} categories: {', '.join(by_category.keys())}",
        speak_text_uk=f"У мене {len(actions)} команд у {len(by_category)} категоріях: {', '.join(by_category.keys())}",
    )


@registry.register(
    name="stop_assistant",
    category="conversation",
    description_en="Shut down the assistant",
    description_uk="Вимкнути помічника",
)
def stop_assistant() -> ActionResult:
    """Request assistant shutdown."""
    if _state_ref:
        _state_ref.shutdown()

    return ActionResult(
        success=True,
        message="Shutting down",
        speak_text_en="Goodbye!",
        speak_text_uk="До побачення!",
    )
