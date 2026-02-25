"""Tests for Ollama brain engine (mocked HTTP)."""

import json
from unittest.mock import patch, MagicMock

import pytest

from kabolai.brain.ollama_brain import OllamaBrain
from kabolai.brain.models import BrainResponse


@pytest.fixture
def brain():
    return OllamaBrain(
        base_url="http://localhost:11434",
        model="test-model",
        temperature=0.1,
        timeout=10,
    )


class TestOllamaBrain:
    @patch("kabolai.brain.ollama_brain.requests.post")
    def test_process_command(self, mock_post, brain):
        """Test parsing a command from LLM response."""
        # Import actions to populate registry
        import kabolai.actions.apps  # noqa
        import kabolai.actions.system  # noqa

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": json.dumps({
                    "command": {
                        "action": "open_app",
                        "params": {"app_name": "notepad"},
                        "confidence": 0.95,
                    },
                    "response_text": "Opening notepad",
                    "is_conversation": False,
                })
            }
        }
        mock_post.return_value = mock_response

        result = brain.process("open notepad", "en")
        assert isinstance(result, BrainResponse)
        assert result.command is not None
        assert result.command.action == "open_app"
        assert result.command.params["app_name"] == "notepad"

    @patch("kabolai.brain.ollama_brain.requests.post")
    def test_process_conversation(self, mock_post, brain):
        """Test parsing a conversational response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": json.dumps({
                    "command": None,
                    "response_text": "I'm doing great!",
                    "is_conversation": True,
                })
            }
        }
        mock_post.return_value = mock_response

        result = brain.process("how are you?", "en")
        assert result.is_conversation is True
        assert result.command is None

    @patch("kabolai.brain.ollama_brain.requests.post")
    def test_process_connection_error(self, mock_post, brain):
        """Test handling when Ollama is not reachable."""
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("refused")

        result = brain.process("hello", "en")
        assert result.is_conversation is True
        assert "Ollama" in result.response_text

    @patch("kabolai.brain.ollama_brain.requests.post")
    def test_process_timeout(self, mock_post, brain):
        """Test handling request timeout."""
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout("timeout")

        result = brain.process("hello", "en")
        assert result.is_conversation is True
        assert "timeout" in result.response_text.lower() or "timed out" in result.response_text.lower()

    @patch("kabolai.brain.ollama_brain.requests.post")
    def test_process_invalid_json(self, mock_post, brain):
        """Test handling malformed JSON from LLM."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "not valid json at all"}
        }
        mock_post.return_value = mock_response

        result = brain.process("hello", "en")
        assert result.is_conversation is True
        assert "trouble" in result.response_text.lower() or "sorry" in result.response_text.lower()

    @patch("kabolai.brain.ollama_brain.requests.get")
    def test_is_available_true(self, mock_get, brain):
        """Test availability check when Ollama is running."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "test-model:latest"}]
        }
        mock_get.return_value = mock_response

        assert brain.is_available() is True

    @patch("kabolai.brain.ollama_brain.requests.get")
    def test_is_available_false(self, mock_get, brain):
        """Test availability check when Ollama is down."""
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError()

        assert brain.is_available() is False

    @patch("kabolai.brain.ollama_brain.requests.post")
    def test_process_ukrainian(self, mock_post, brain):
        """Test processing Ukrainian input."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": json.dumps({
                    "command": {
                        "action": "get_time",
                        "params": {},
                        "confidence": 0.99,
                    },
                    "response_text": "Зараз перевірю",
                    "is_conversation": False,
                })
            }
        }
        mock_post.return_value = mock_response

        result = brain.process("Котра година?", "uk")
        assert result.command.action == "get_time"
