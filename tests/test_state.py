"""Tests for assistant state with self-healing features."""

import threading
import time

from kabolai.core.state import AssistantState


class TestAssistantState:
    def test_initial_state(self):
        state = AssistantState()
        assert state.language == "en"
        assert state.is_active is True
        assert state.is_listening is False
        assert state.is_processing is False
        assert state.is_speaking is False
        assert state.is_running is True
        assert state.is_busy is False

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

    def test_set_processing(self):
        state = AssistantState()
        state.set_processing(True)
        assert state.is_processing is True
        state.set_processing(False)
        assert state.is_processing is False

    def test_set_speaking(self):
        state = AssistantState()
        state.set_speaking(True)
        assert state.is_speaking is True
        assert state.is_busy is True
        state.set_speaking(False)
        assert state.is_speaking is False

    def test_shutdown(self):
        state = AssistantState()
        state.shutdown()
        assert state.is_running is False
        assert state.is_active is False
        assert state.is_listening is False
        assert state.is_processing is False
        assert state.is_speaking is False

    def test_is_busy(self):
        state = AssistantState()
        assert state.is_busy is False
        state.set_listening(True)
        assert state.is_busy is True
        state.set_listening(False)
        state.set_processing(True)
        assert state.is_busy is True
        state.set_processing(False)
        state.set_speaking(True)
        assert state.is_busy is True

    def test_pipeline_lock(self):
        state = AssistantState()
        # First acquire should succeed
        assert state.try_start_pipeline() is True
        # Second should fail (pipeline busy)
        assert state.try_start_pipeline() is False
        # Release
        state.end_pipeline()
        # Now should succeed again
        assert state.try_start_pipeline() is True
        state.end_pipeline()

    def test_end_pipeline_clears_all(self):
        state = AssistantState()
        state.try_start_pipeline()
        state.set_listening(True)
        state.set_processing(True)
        state.set_speaking(True)
        state.end_pipeline()
        assert state.is_listening is False
        assert state.is_processing is False
        assert state.is_speaking is False
        assert state.is_busy is False

    def test_force_reset(self):
        state = AssistantState()
        state.set_listening(True)
        state.set_processing(True)
        state.set_speaking(True)
        state.force_reset()
        assert state.is_listening is False
        assert state.is_processing is False
        assert state.is_speaking is False
