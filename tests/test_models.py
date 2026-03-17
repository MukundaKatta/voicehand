"""Tests for data models."""

from voicehand.models import Action, ActionType, AppContext, Macro, VoiceCommand


class TestAction:
    def test_describe(self):
        action = Action(action_type=ActionType.OPEN_APP, target="Chrome")
        desc = action.describe()
        assert "open_app" in desc
        assert "Chrome" in desc

    def test_defaults(self):
        action = Action(action_type=ActionType.COPY)
        assert action.target is None
        assert action.confidence == 1.0


class TestVoiceCommand:
    def test_primary_action(self):
        cmd = VoiceCommand(
            raw_text="test",
            actions=[Action(action_type=ActionType.COPY)],
        )
        assert cmd.primary_action.action_type == ActionType.COPY

    def test_primary_action_empty(self):
        cmd = VoiceCommand(raw_text="test", actions=[])
        assert cmd.primary_action is None


class TestMacro:
    def test_matches(self):
        macro = Macro(
            name="test",
            trigger_phrases=["hello world"],
            actions=[Action(action_type=ActionType.COPY)],
        )
        assert macro.matches("hello world") is True
        assert macro.matches("say hello world now") is True
        assert macro.matches("goodbye") is False


class TestAppContext:
    def test_is_browser(self):
        ctx = AppContext(app_name="Chrome")
        assert ctx.is_browser() is True

    def test_is_editor(self):
        ctx = AppContext(app_name="Code")
        assert ctx.is_editor() is True

    def test_is_terminal(self):
        ctx = AppContext(app_name="Terminal")
        assert ctx.is_terminal() is True

    def test_not_browser(self):
        ctx = AppContext(app_name="Slack")
        assert ctx.is_browser() is False
