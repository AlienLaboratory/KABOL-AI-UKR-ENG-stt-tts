"""Web browser actions."""

import logging
import urllib.parse
import webbrowser

from kabolai.actions.base import ActionResult
from kabolai.actions.registry import registry

logger = logging.getLogger(__name__)


@registry.register(
    name="web_search",
    category="web",
    description_en="Search the web using default browser",
    description_uk="Пошук в інтернеті через браузер",
    parameters=[
        {"name": "query", "type": "str", "required": True,
         "description": "Search query text"}
    ],
)
def web_search(query: str) -> ActionResult:
    """Open a web search in the default browser."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://duckduckgo.com/?q={encoded}"

    try:
        webbrowser.open(url)
        return ActionResult(
            success=True,
            message=f"Searching for: {query}",
            speak_text_en=f"Searching for {query}",
            speak_text_uk=f"Шукаю {query}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Failed to open browser: {e}",
            speak_text_en="Sorry, I could not open the browser",
            speak_text_uk="Вибачте, не можу відкрити браузер",
        )


@registry.register(
    name="open_url",
    category="web",
    description_en="Open a specific URL in the default browser",
    description_uk="Відкрити URL в браузері",
    parameters=[
        {"name": "url", "type": "str", "required": True,
         "description": "The URL to open"}
    ],
)
def open_url(url: str) -> ActionResult:
    """Open a URL in the default browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return ActionResult(
            success=True,
            message=f"Opened {url}",
            speak_text_en=f"Opening the website",
            speak_text_uk=f"Відкриваю сайт",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Failed to open URL: {e}",
            speak_text_en="Sorry, I could not open that URL",
            speak_text_uk="Вибачте, не можу відкрити цю адресу",
        )
