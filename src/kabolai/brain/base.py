"""Abstract base class for the LLM brain."""

from abc import ABC, abstractmethod
from typing import Optional

from kabolai.brain.models import BrainResponse


class BrainEngine(ABC):
    """Abstract LLM brain for natural language understanding."""

    @abstractmethod
    def process(
        self,
        user_text: str,
        language: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> BrainResponse:
        """Parse user text into a structured command."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM backend is reachable."""
        ...

    def cleanup(self) -> None:
        """Release resources."""
        pass
