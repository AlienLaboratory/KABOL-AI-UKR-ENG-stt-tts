"""Tests for assistant state."""

from kabolai.core.state import AssistantState


class TestAssistantState:
    def test_initial_state(self):
        state = AssistantState()
        assert state.language == "en"
        assert state.is_active is True
        assert state.is_listening is False
        assert state.is_running is True

    def test_toggle_language(self):
        state = AssistantState(language="en")
        assert state.toggle_language() == "uk"
        assert state.language == "uk"
        assert state.toggle_language() == "en"
        assert state.language == "en"

    def test_set_language(self):
        state = AssistantState()
        state.set_language("uk")
        assert state.language == "uk"
        state.set_language("invalid")
        assert state.language == "uk"  # unchanged

    def test_toggle_active(self):
        state = AssistantState()
        assert state.toggle_active() is False
        assert state.is_active is False
        assert state.toggle_active() is True

    def test_set_listening(self):
        state = AssistantState()
        state.set_listening(True)
        assert state.is_listening is True
        state.set_listening(False)
        assert state.is_listening is False

    def test_shutdown(self):
        state = AssistantState()
        state.shutdown()
        assert state.is_running is False
        assert state.is_active is False
