"""Ollama-based brain engine for intent parsing."""

import json
import logging
from typing import Optional

import requests

from kabolai.brain.base import BrainEngine
from kabolai.brain.models import BrainResponse, ParsedCommand
from kabolai.brain.prompts import build_system_prompt
from kabolai.actions.registry import registry

logger = logging.getLogger(__name__)


class OllamaBrain(BrainEngine):
    """Brain that uses Ollama local LLM for intent parsing."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:1.5b",
        temperature: float = 0.1,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def process(
        self,
        user_text: str,
        language: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> BrainResponse:
        """Parse user text into a structured command via Ollama."""
        actions_schema = registry.get_schema_for_llm(language)
        system_prompt = build_system_prompt(language, actions_schema)

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_text})

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "format": BrainResponse.model_json_schema(),
                    "options": {
                        "temperature": self.temperature,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["message"]["content"]

            return BrainResponse.model_validate_json(content)

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running?")
            msg = (
                "Не можу з'єднатися з Ollama. Переконайтеся, що вона запущена."
                if language == "uk"
                else "Cannot connect to Ollama. Please make sure it is running."
            )
            return BrainResponse(response_text=msg, is_conversation=True)

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out.")
            msg = (
                "Запит до Ollama перевищив час очікування."
                if language == "uk"
                else "Ollama request timed out. The model may be loading."
            )
            return BrainResponse(response_text=msg, is_conversation=True)

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Brain processing error: {e}", exc_info=True)
            msg = (
                "Вибачте, у мене виникли проблеми з розумінням."
                if language == "uk"
                else "Sorry, I had trouble understanding that."
            )
            return BrainResponse(response_text=msg, is_conversation=True)

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code != 200:
                return False
            tags = r.json()
            models = [m["name"] for m in tags.get("models", [])]
            # Check if our model (or a variant) is available
            return any(self.model in m or m.startswith(self.model.split(":")[0])
                       for m in models)
        except Exception:
            return False

    def cleanup(self) -> None:
        pass
