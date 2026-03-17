"""Tests for SpeechProcessor."""

import pytest

from voicehand.models import ActionType
from voicehand.recognition.processor import SpeechProcessor


@pytest.fixture
def processor():
    return SpeechProcessor()


class TestNormalisation:
    def test_strip_filler_words(self, processor):
        cmd = processor.process("um like open Chrome")
        assert cmd.actions[0].action_type == ActionType.OPEN_APP

    def test_correct_app_name(self, processor):
        cmd = processor.process("open vs code")
        assert cmd.actions[0].target == "Visual Studio Code"

    def test_correct_firefox(self, processor):
        cmd = processor.process("open fire fox")
        assert cmd.actions[0].target == "Firefox"


class TestMacroFallback:
    def test_macro_matched_first(self, processor):
        cmd = processor.process("morning routine")
        assert cmd.is_macro
        assert cmd.macro_name == "morning_routine"

    def test_parser_used_when_no_macro(self, processor):
        cmd = processor.process("open Safari")
        assert not cmd.is_macro
        assert cmd.actions[0].action_type == ActionType.OPEN_APP


class TestContextEnrichment:
    def test_context_recorded(self, processor):
        processor.process("open Chrome")
        history = processor.context_tracker._context.history
        assert len(history) >= 1
