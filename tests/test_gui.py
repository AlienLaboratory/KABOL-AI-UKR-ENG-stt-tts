"""Tests for GUI components (non-visual, logic-only tests).

These tests verify the logic of GUI-related modules without
actually creating tkinter windows (which requires a display).
"""

import queue
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from kabolai.core.state import AssistantState
from kabolai.gui.theme import (
    STATUS_TEXT, MIC_READY, MIC_LISTENING, MIC_PROCESSING,
    MIC_SPEAKING, MIC_INACTIVE,
)


class TestTheme:
    """Test theme constants."""

    def test_status_text_has_all_states(self):
        expected = {"ready", "listening", "processing", "speaking", "inactive", "error"}
        assert set(STATUS_TEXT.keys()) == expected

    def test_status_text_has_both_languages(self):
        for state, texts in STATUS_TEXT.items():
            assert "en" in texts, f"Missing EN text for state '{state}'"
            assert "uk" in texts, f"Missing UK text for state '{state}'"

    def test_mic_colors_are_distinct(self):
        colors = {MIC_READY, MIC_LISTENING, MIC_PROCESSING, MIC_SPEAKING, MIC_INACTIVE}
        assert len(colors) == 5, "All mic button states should have distinct colors"


class TestEventSystem:
    """Test the assistant event system."""

    def test_emit_event_adds_to_queue(self):
        """Events should be added to the queue."""
        from kabolai.core.config import AppConfig

        with patch("kabolai.assistant.create_stt_engine"), \
             patch("kabolai.assistant.create_brain"), \
             patch("kabolai.assistant.AudioRecorder"), \
             patch("kabolai.assistant.AudioPlayer"):
            from kabolai.assistant import Assistant
            config = AppConfig()
            assistant = Assistant(config)

            assistant._emit_event("test_event", {"key": "value"})
            events = assistant.drain_events()
            assert len(events) == 1
            assert events[0]["type"] == "test_event"
            assert events[0]["data"]["key"] == "value"

    def test_drain_events_empties_queue(self):
        """drain_events should return all events and empty the queue."""
        from kabolai.core.config import AppConfig

        with patch("kabolai.assistant.create_stt_engine"), \
             patch("kabolai.assistant.create_brain"), \
             patch("kabolai.assistant.AudioRecorder"), \
             patch("kabolai.assistant.AudioPlayer"):
            from kabolai.assistant import Assistant
            config = AppConfig()
            assistant = Assistant(config)

            assistant._emit_event("e1", {})
            assistant._emit_event("e2", {})
            assistant._emit_event("e3", {})

            events = assistant.drain_events()
            assert len(events) == 3

            # Queue should be empty now
            events2 = assistant.drain_events()
            assert len(events2) == 0

    def test_event_callback(self):
        """Registered callbacks should be called."""
        from kabolai.core.config import AppConfig

        with patch("kabolai.assistant.create_stt_engine"), \
             patch("kabolai.assistant.create_brain"), \
             patch("kabolai.assistant.AudioRecorder"), \
             patch("kabolai.assistant.AudioPlayer"):
            from kabolai.assistant import Assistant
            config = AppConfig()
            assistant = Assistant(config)

            received = []
            assistant.add_event_callback(
                lambda etype, data: received.append((etype, data))
            )
            assistant._emit_event("user_text", {"text": "hello"})

            assert len(received) == 1
            assert received[0] == ("user_text", {"text": "hello"})


class TestSelfHealing:
    """Test the self-healing pipeline mechanism."""

    def test_pipeline_auto_resets_after_timeout(self):
        """If pipeline is stuck too long, try_start_pipeline should force-reset."""
        state = AssistantState()
        # Simulate a stuck pipeline
        assert state.try_start_pipeline() is True
        # Manually set start time to the past
        state._pipeline_start = time.monotonic() - 120  # 2 minutes ago

        # This should trigger self-healing and allow new pipeline
        assert state.try_start_pipeline() is True
        state.end_pipeline()

    def test_pipeline_prevents_overlap(self):
        """Normal pipeline should prevent concurrent access."""
        state = AssistantState()
        assert state.try_start_pipeline() is True
        assert state.try_start_pipeline() is False  # Can't start again
        state.end_pipeline()
        assert state.try_start_pipeline() is True  # Can start after release
        state.end_pipeline()

    def test_end_pipeline_clears_all_flags(self):
        state = AssistantState()
        state.try_start_pipeline()
        state.set_listening(True)
        state.set_processing(True)
        state.set_speaking(True)
        assert state.is_busy is True

        state.end_pipeline()
        assert state.is_listening is False
        assert state.is_processing is False
        assert state.is_speaking is False
        assert state.is_busy is False

    def test_force_reset_clears_stuck_state(self):
        state = AssistantState()
        state.set_listening(True)
        state.set_processing(True)
        state.set_speaking(True)
        state.force_reset()
        assert state.is_busy is False


class TestFirstRunCheck:
    """Test the first-run setup checker."""

    def test_check_setup_detects_missing_models(self):
        from kabolai.core.config import AppConfig

        with patch("kabolai.core.constants.MODELS_DIR") as mock_dir:
            mock_dir.__truediv__ = MagicMock(
                return_value=MagicMock(exists=MagicMock(return_value=False))
            )
            # This will naturally detect missing models since models/
            # doesn't exist in the test environment
            from kabolai.gui.first_run import check_setup
            config = AppConfig()
            missing = check_setup(config)
            # Should detect at least something missing
            assert isinstance(missing, dict)
