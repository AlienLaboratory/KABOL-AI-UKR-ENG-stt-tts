"""Pydantic models for structured LLM output."""

from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


class ParsedCommand(BaseModel):
    """Structured command parsed by the LLM."""
    action: str = Field(description="Action name from the registry")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class BrainResponse(BaseModel):
    """Full response from the brain engine."""
    command: Optional[ParsedCommand] = None
    response_text: str = Field(description="Text to speak back to user")
    is_conversation: bool = Field(
        default=False,
        description="True if just conversation, no action needed",
    )
