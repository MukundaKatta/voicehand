"""Tests for MacroManager."""

import pytest

from voicehand.commands.macros import MacroManager
from voicehand.models import Action, ActionType, Macro


@pytest.fixture
def manager():
    return MacroManager()


class TestDefaults:
    def test_has_default_macros(self, manager):
        macros = manager.list_macros()
        assert len(macros) >= 5

    def test_morning_routine_exists(self, manager):
        macro = manager.get("morning_routine")
        assert macro is not None
        assert len(macro.actions) == 3


class TestMatch:
    def test_match_morning_routine(self, manager):
        cmd = manager.match("morning routine")
        assert cmd is not None
        assert cmd.is_macro
        assert cmd.macro_name == "morning_routine"

    def test_match_coding_setup(self, manager):
        cmd = manager.match("start coding")
        assert cmd is not None
        assert cmd.macro_name == "coding_setup"

    def test_no_match(self, manager):
        cmd = manager.match("xyzzy nonsense")
        assert cmd is None

    def test_match_increments_usage(self, manager):
        macro = manager.get("morning_routine")
        before = macro.usage_count
        manager.match("morning routine")
        assert macro.usage_count == before + 1


class TestRegister:
    def test_register_custom_macro(self, manager):
        macro = Macro(
            name="test_macro",
            trigger_phrases=["run test"],
            actions=[Action(action_type=ActionType.OPEN_APP, target="Terminal")],
        )
        manager.register(macro)
        assert manager.get("test_macro") is not None

    def test_unregister(self, manager):
        assert manager.unregister("morning_routine") is True
        assert manager.get("morning_routine") is None

    def test_unregister_nonexistent(self, manager):
        assert manager.unregister("does_not_exist") is False


class TestDisabled:
    def test_disabled_macro_no_match(self, manager):
        macro = manager.get("morning_routine")
        macro.enabled = False
        cmd = manager.match("morning routine")
        assert cmd is None
