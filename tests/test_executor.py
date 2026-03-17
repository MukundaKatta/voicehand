"""Tests for CommandExecutor."""

import pytest

from voicehand.commands.executor import CommandExecutor
from voicehand.models import Action, ActionType, ClickType, ScrollDirection, VoiceCommand


@pytest.fixture
def executor():
    return CommandExecutor(dry_run=True)


class TestDryRun:
    def test_open_app(self, executor):
        action = Action(action_type=ActionType.OPEN_APP, target="Chrome")
        result = executor.execute_action(action)
        assert result.success
        assert "dry-run" in result.message
        assert "Chrome" in result.message

    def test_type_text(self, executor):
        action = Action(action_type=ActionType.TYPE_TEXT, value="hello")
        result = executor.execute_action(action)
        assert result.success
        assert "hello" in result.message

    def test_click(self, executor):
        action = Action(action_type=ActionType.CLICK, target="button")
        result = executor.execute_action(action)
        assert result.success

    def test_right_click(self, executor):
        action = Action(action_type=ActionType.CLICK, target="menu", click_type=ClickType.RIGHT)
        result = executor.execute_action(action)
        assert result.success
        assert "right" in result.message

    def test_scroll_up(self, executor):
        action = Action(action_type=ActionType.SCROLL, scroll_direction=ScrollDirection.UP, scroll_amount=5)
        result = executor.execute_action(action)
        assert result.success
        assert "up" in result.message

    def test_navigate(self, executor):
        action = Action(action_type=ActionType.NAVIGATE, target="google.com")
        result = executor.execute_action(action)
        assert result.success
        assert "google.com" in result.message

    def test_switch_window(self, executor):
        action = Action(action_type=ActionType.SWITCH_WINDOW, target="Slack")
        result = executor.execute_action(action)
        assert result.success

    def test_copy(self, executor):
        action = Action(action_type=ActionType.COPY)
        result = executor.execute_action(action)
        assert result.success

    def test_paste(self, executor):
        action = Action(action_type=ActionType.PASTE)
        result = executor.execute_action(action)
        assert result.success

    def test_screenshot(self, executor):
        action = Action(action_type=ActionType.SCREENSHOT)
        result = executor.execute_action(action)
        assert result.success

    def test_volume_up(self, executor):
        action = Action(action_type=ActionType.VOLUME_UP)
        result = executor.execute_action(action)
        assert result.success

    def test_press_key(self, executor):
        action = Action(action_type=ActionType.PRESS_KEY, value="escape")
        result = executor.execute_action(action)
        assert result.success
        assert "escape" in result.message

    def test_lock_screen(self, executor):
        action = Action(action_type=ActionType.LOCK_SCREEN)
        result = executor.execute_action(action)
        assert result.success

    def test_search(self, executor):
        action = Action(action_type=ActionType.SEARCH, value="test query")
        result = executor.execute_action(action)
        assert result.success


class TestExecuteCommand:
    def test_execute_full_command(self, executor):
        command = VoiceCommand(
            raw_text="open Chrome and scroll down",
            actions=[
                Action(action_type=ActionType.OPEN_APP, target="Chrome"),
                Action(action_type=ActionType.SCROLL, scroll_direction=ScrollDirection.DOWN),
            ],
        )
        report = executor.execute(command)
        assert report.all_succeeded
        assert len(report.results) == 2

    def test_report_summary(self, executor):
        command = VoiceCommand(
            raw_text="test",
            actions=[Action(action_type=ActionType.COPY)],
        )
        report = executor.execute(command)
        assert "1 succeeded" in report.summary
