"""Tests for CommandParser."""

import pytest

from voicehand.commands.parser import CommandParser
from voicehand.models import ActionType, ClickType, ScrollDirection


@pytest.fixture
def parser():
    return CommandParser()


class TestOpenApp:
    def test_open_chrome(self, parser):
        cmd = parser.parse("open Chrome")
        assert len(cmd.actions) == 1
        assert cmd.actions[0].action_type == ActionType.OPEN_APP
        assert cmd.actions[0].target == "Chrome"

    def test_launch_spotify(self, parser):
        cmd = parser.parse("launch Spotify")
        assert cmd.actions[0].action_type == ActionType.OPEN_APP
        assert cmd.actions[0].target == "Spotify"

    def test_start_terminal(self, parser):
        cmd = parser.parse("start Terminal")
        assert cmd.actions[0].action_type == ActionType.OPEN_APP

    def test_run_finder(self, parser):
        cmd = parser.parse("run Finder")
        assert cmd.actions[0].action_type == ActionType.OPEN_APP


class TestTypeText:
    def test_type_hello(self, parser):
        cmd = parser.parse("type hello world")
        assert cmd.actions[0].action_type == ActionType.TYPE_TEXT
        assert cmd.actions[0].value == "hello world"

    def test_write_message(self, parser):
        cmd = parser.parse("write meeting at 3pm")
        assert cmd.actions[0].action_type == ActionType.TYPE_TEXT

    def test_enter_text(self, parser):
        cmd = parser.parse("enter text search query")
        assert cmd.actions[0].action_type == ActionType.TYPE_TEXT

    def test_dictate(self, parser):
        cmd = parser.parse("dictate the quick brown fox")
        assert cmd.actions[0].action_type == ActionType.TYPE_TEXT


class TestClick:
    def test_click_on_button(self, parser):
        cmd = parser.parse("click on submit")
        assert cmd.actions[0].action_type == ActionType.CLICK
        assert cmd.actions[0].target == "submit"

    def test_right_click(self, parser):
        cmd = parser.parse("right click on file")
        assert cmd.actions[0].action_type == ActionType.CLICK
        assert cmd.actions[0].click_type == ClickType.RIGHT

    def test_double_click(self, parser):
        cmd = parser.parse("double click on icon")
        assert cmd.actions[0].action_type == ActionType.CLICK
        assert cmd.actions[0].click_type == ClickType.DOUBLE

    def test_tap(self, parser):
        cmd = parser.parse("tap on settings")
        assert cmd.actions[0].action_type == ActionType.CLICK


class TestScroll:
    def test_scroll_up(self, parser):
        cmd = parser.parse("scroll up")
        assert cmd.actions[0].action_type == ActionType.SCROLL
        assert cmd.actions[0].scroll_direction == ScrollDirection.UP

    def test_scroll_down(self, parser):
        cmd = parser.parse("scroll down")
        assert cmd.actions[0].action_type == ActionType.SCROLL
        assert cmd.actions[0].scroll_direction == ScrollDirection.DOWN

    def test_scroll_with_amount(self, parser):
        cmd = parser.parse("scroll up 5")
        assert cmd.actions[0].scroll_amount == 5

    def test_page_down(self, parser):
        cmd = parser.parse("page down")
        assert cmd.actions[0].action_type == ActionType.SCROLL
        assert cmd.actions[0].scroll_amount == 10


class TestNavigation:
    def test_go_to(self, parser):
        cmd = parser.parse("go to google.com")
        assert cmd.actions[0].action_type == ActionType.NAVIGATE
        assert cmd.actions[0].target == "google.com"

    def test_navigate_to(self, parser):
        cmd = parser.parse("navigate to github.com")
        assert cmd.actions[0].action_type == ActionType.NAVIGATE

    def test_switch_to(self, parser):
        cmd = parser.parse("switch to Slack")
        assert cmd.actions[0].action_type == ActionType.SWITCH_WINDOW


class TestShortcuts:
    def test_copy(self, parser):
        cmd = parser.parse("copy that")
        assert cmd.actions[0].action_type == ActionType.COPY

    def test_paste(self, parser):
        cmd = parser.parse("paste")
        assert cmd.actions[0].action_type == ActionType.PASTE

    def test_undo(self, parser):
        cmd = parser.parse("undo that")
        assert cmd.actions[0].action_type == ActionType.UNDO

    def test_redo(self, parser):
        cmd = parser.parse("redo")
        assert cmd.actions[0].action_type == ActionType.REDO

    def test_save(self, parser):
        cmd = parser.parse("save file")
        assert cmd.actions[0].action_type == ActionType.SAVE


class TestBrowser:
    def test_new_tab(self, parser):
        cmd = parser.parse("new tab")
        assert cmd.actions[0].action_type == ActionType.NEW_TAB

    def test_refresh(self, parser):
        cmd = parser.parse("refresh the page")
        assert cmd.actions[0].action_type == ActionType.REFRESH

    def test_go_back(self, parser):
        cmd = parser.parse("go back")
        assert cmd.actions[0].action_type == ActionType.GO_BACK

    def test_search(self, parser):
        cmd = parser.parse("search for python tutorials")
        assert cmd.actions[0].action_type == ActionType.SEARCH
        assert cmd.actions[0].value == "python tutorials"


class TestSystem:
    def test_screenshot(self, parser):
        cmd = parser.parse("take a screenshot")
        assert cmd.actions[0].action_type == ActionType.SCREENSHOT

    def test_volume_up(self, parser):
        cmd = parser.parse("volume up")
        assert cmd.actions[0].action_type == ActionType.VOLUME_UP

    def test_mute(self, parser):
        cmd = parser.parse("mute the sound")
        assert cmd.actions[0].action_type == ActionType.MUTE

    def test_lock_screen(self, parser):
        cmd = parser.parse("lock the screen")
        assert cmd.actions[0].action_type == ActionType.LOCK_SCREEN


class TestCompound:
    def test_two_actions(self, parser):
        cmd = parser.parse("open Chrome and then go to google.com")
        assert len(cmd.actions) == 2
        assert cmd.actions[0].action_type == ActionType.OPEN_APP
        assert cmd.actions[1].action_type == ActionType.NAVIGATE

    def test_three_actions(self, parser):
        cmd = parser.parse("open Safari then navigate to github.com then scroll down")
        assert len(cmd.actions) == 3


class TestEdgeCases:
    def test_empty_string(self, parser):
        cmd = parser.parse("")
        assert cmd.actions == []
        assert cmd.confidence == 0.0

    def test_unrecognised(self, parser):
        cmd = parser.parse("xyzzy foobar")
        assert cmd.actions == []

    def test_confidence_present(self, parser):
        cmd = parser.parse("open Chrome")
        assert cmd.confidence > 0

    def test_get_supported_patterns(self, parser):
        patterns = parser.get_supported_patterns()
        assert len(patterns) >= 50
