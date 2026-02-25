"""Tests for action modules."""

import datetime
from unittest.mock import patch, MagicMock

import pytest


class TestSystemActions:
    def test_get_time(self):
        from kabolai.actions.system import get_time

        result = get_time()
        assert result.success is True
        assert result.speak_text_en is not None
        assert result.speak_text_uk is not None

    def test_get_date(self):
        from kabolai.actions.system import get_date

        result = get_date()
        assert result.success is True
        assert str(datetime.datetime.now().year) in result.message

    def test_get_system_info(self):
        from kabolai.actions.system import get_system_info

        result = get_system_info()
        assert result.success is True
        assert result.data is not None
        assert "cpu_percent" in result.data
        assert "ram_total_gb" in result.data

    def test_get_ip_address(self):
        from kabolai.actions.system import get_ip_address

        result = get_ip_address()
        assert result.success is True
        assert result.data is not None
        assert "ip" in result.data


class TestWebActions:
    @patch("webbrowser.open")
    def test_web_search(self, mock_open):
        from kabolai.actions.web import web_search

        result = web_search("python tutorials")
        assert result.success is True
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        assert "python+tutorials" in url

    @patch("webbrowser.open")
    def test_open_url(self, mock_open):
        from kabolai.actions.web import open_url

        result = open_url("example.com")
        assert result.success is True
        mock_open.assert_called_once_with("https://example.com")

    @patch("webbrowser.open")
    def test_open_url_with_https(self, mock_open):
        from kabolai.actions.web import open_url

        result = open_url("https://google.com")
        assert result.success is True
        mock_open.assert_called_once_with("https://google.com")


class TestAppActions:
    @patch("subprocess.Popen")
    def test_open_app_known(self, mock_popen):
        from kabolai.actions.apps import open_app

        result = open_app("notepad")
        assert result.success is True
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_open_app_unknown(self, mock_popen):
        from kabolai.actions.apps import open_app

        result = open_app("my_custom_app")
        assert result.success is True
        mock_popen.assert_called()

    @patch("subprocess.Popen", side_effect=FileNotFoundError("not found"))
    def test_open_app_failure(self, mock_popen):
        from kabolai.actions.apps import open_app

        result = open_app("nonexistent_app_xyz")
        assert result.success is False


class TestConversationActions:
    def test_list_commands(self):
        import kabolai.actions.apps  # noqa
        import kabolai.actions.system  # noqa
        import kabolai.actions.web  # noqa
        import kabolai.actions.media  # noqa
        from kabolai.actions.conversation import list_commands

        result = list_commands()
        assert result.success is True
        assert result.data is not None
        assert len(result.data) > 0

    def test_switch_language(self):
        from kabolai.core.state import AssistantState
        from kabolai.actions.conversation import switch_language, set_state_ref

        state = AssistantState(language="en")
        set_state_ref(state)

        result = switch_language("uk")
        assert result.success is True
        assert state.language == "uk"

    def test_switch_language_toggle(self):
        from kabolai.core.state import AssistantState
        from kabolai.actions.conversation import switch_language, set_state_ref

        state = AssistantState(language="en")
        set_state_ref(state)

        result = switch_language()
        assert result.success is True
        assert state.language == "uk"
