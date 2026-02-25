"""Tests for brain Pydantic models and prompt generation."""

import json
import pytest

from kabolai.brain.models import BrainResponse, ParsedCommand
from kabolai.brain.prompts import build_system_prompt


class TestParsedCommand:
    def test_basic_command(self):
        cmd = ParsedCommand(action="open_app", params={"app_name": "notepad"})
        assert cmd.action == "open_app"
        assert cmd.params["app_name"] == "notepad"
        assert cmd.confidence == 1.0

    def test_with_confidence(self):
        cmd = ParsedCommand(action="test", confidence=0.85)
        assert cmd.confidence == 0.85

    def test_empty_params(self):
        cmd = ParsedCommand(action="get_time")
        assert cmd.params == {}


class TestBrainResponse:
    def test_conversation_response(self):
        resp = BrainResponse(
            response_text="I'm doing great!",
            is_conversation=True,
        )
        assert resp.command is None
        assert resp.is_conversation is True

    def test_command_response(self):
        resp = BrainResponse(
            command=ParsedCommand(
                action="open_app",
                params={"app_name": "calculator"},
                confidence=0.95,
            ),
            response_text="Opening calculator",
            is_conversation=False,
        )
        assert resp.command is not None
        assert resp.command.action == "open_app"
        assert resp.is_conversation is False

    def test_json_roundtrip(self):
        resp = BrainResponse(
            command=ParsedCommand(action="get_time"),
            response_text="Checking time",
            is_conversation=False,
        )
        json_str = resp.model_dump_json()
        parsed = BrainResponse.model_validate_json(json_str)
        assert parsed.command.action == "get_time"

    def test_parse_llm_output(self):
        """Simulate parsing what an LLM would return."""
        llm_output = json.dumps({
            "command": {
                "action": "web_search",
                "params": {"query": "python tutorials"},
                "confidence": 0.92,
            },
            "response_text": "Searching for Python tutorials",
            "is_conversation": False,
        })
        resp = BrainResponse.model_validate_json(llm_output)
        assert resp.command.action == "web_search"
        assert resp.command.params["query"] == "python tutorials"

    def test_parse_conversation_output(self):
        llm_output = json.dumps({
            "command": None,
            "response_text": "I'm doing well, thank you!",
            "is_conversation": True,
        })
        resp = BrainResponse.model_validate_json(llm_output)
        assert resp.command is None
        assert resp.is_conversation is True

    def test_json_schema(self):
        schema = BrainResponse.model_json_schema()
        assert "properties" in schema
        assert "response_text" in schema["properties"]


class TestPrompts:
    def test_build_english_prompt(self):
        schema = "- open_app(app_name: str): Open an application"
        prompt = build_system_prompt("en", schema)
        assert "KA-BOL-AI" in prompt
        assert "open_app" in prompt
        assert "JSON" in prompt

    def test_build_ukrainian_prompt(self):
        schema = "- open_app(app_name: str): Відкрити програму"
        prompt = build_system_prompt("uk", schema)
        assert "KA-BOL-AI" in prompt
        assert "open_app" in prompt
        assert "JSON" in prompt
