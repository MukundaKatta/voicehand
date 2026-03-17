"""CommandExecutor - simulates OS actions from parsed commands."""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass, field

from voicehand.models import Action, ActionType, ClickType, ScrollDirection, VoiceCommand

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing an action."""

    success: bool
    action: Action
    message: str = ""
    error: str | None = None


@dataclass
class ExecutionReport:
    """Report covering all actions in a command execution."""

    results: list[ExecutionResult] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def summary(self) -> str:
        ok = sum(1 for r in self.results if r.success)
        fail = len(self.results) - ok
        return f"{ok} succeeded, {fail} failed out of {len(self.results)} actions"


class CommandExecutor:
    """Simulates OS-level actions for voice commands.

    By default operates in dry-run mode, logging what would happen
    without actually performing the actions. Set ``dry_run=False``
    to execute actions for real (requires pyautogui and platform support).
    """

    def __init__(self, *, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._handlers: dict[ActionType, callable] = {
            ActionType.OPEN_APP: self._open_app,
            ActionType.TYPE_TEXT: self._type_text,
            ActionType.CLICK: self._click,
            ActionType.SCROLL: self._scroll,
            ActionType.NAVIGATE: self._navigate,
            ActionType.SWITCH_WINDOW: self._switch_window,
            ActionType.PRESS_KEY: self._press_key,
            ActionType.SELECT_TEXT: self._select_text,
            ActionType.COPY: self._hotkey_action,
            ActionType.PASTE: self._hotkey_action,
            ActionType.UNDO: self._hotkey_action,
            ActionType.REDO: self._hotkey_action,
            ActionType.SAVE: self._hotkey_action,
            ActionType.CLOSE: self._hotkey_action,
            ActionType.CLOSE_TAB: self._hotkey_action,
            ActionType.MINIMIZE: self._hotkey_action,
            ActionType.MAXIMIZE: self._hotkey_action,
            ActionType.SCREENSHOT: self._screenshot,
            ActionType.VOLUME_UP: self._media_action,
            ActionType.VOLUME_DOWN: self._media_action,
            ActionType.MUTE: self._media_action,
            ActionType.PLAY_PAUSE: self._media_action,
            ActionType.BRIGHTNESS_UP: self._media_action,
            ActionType.BRIGHTNESS_DOWN: self._media_action,
            ActionType.LOCK_SCREEN: self._lock_screen,
            ActionType.SEARCH: self._search,
            ActionType.NEW_TAB: self._hotkey_action,
            ActionType.REFRESH: self._hotkey_action,
            ActionType.GO_BACK: self._hotkey_action,
            ActionType.GO_FORWARD: self._hotkey_action,
        }
        # Modifier key for the current platform
        self._mod = "command" if sys.platform == "darwin" else "ctrl"

    # --- hotkey mappings ---

    def _hotkey_for(self, action_type: ActionType) -> tuple[str, ...]:
        """Return the keyboard shortcut for an action type."""
        mod = self._mod
        mapping: dict[ActionType, tuple[str, ...]] = {
            ActionType.COPY: (mod, "c"),
            ActionType.PASTE: (mod, "v"),
            ActionType.UNDO: (mod, "z"),
            ActionType.REDO: (mod, "shift", "z"),
            ActionType.SAVE: (mod, "s"),
            ActionType.CLOSE: (mod, "w"),
            ActionType.CLOSE_TAB: (mod, "w"),
            ActionType.MINIMIZE: (mod, "m"),
            ActionType.MAXIMIZE: (mod, "shift", "f"),
            ActionType.NEW_TAB: (mod, "t"),
            ActionType.REFRESH: (mod, "r"),
            ActionType.GO_BACK: (mod, "["),
            ActionType.GO_FORWARD: (mod, "]"),
        }
        return mapping.get(action_type, ())

    # --- public API ---

    def execute(self, command: VoiceCommand) -> ExecutionReport:
        """Execute all actions in a VoiceCommand."""
        report = ExecutionReport()
        for action in command.actions:
            result = self.execute_action(action)
            report.results.append(result)
        return report

    def execute_action(self, action: Action) -> ExecutionResult:
        """Execute a single action."""
        handler = self._handlers.get(action.action_type)
        if handler is None:
            return ExecutionResult(
                success=False,
                action=action,
                error=f"No handler for action type: {action.action_type.value}",
            )
        try:
            message = handler(action)
            return ExecutionResult(success=True, action=action, message=message)
        except Exception as exc:
            logger.exception("Action execution failed: %s", action.describe())
            return ExecutionResult(success=False, action=action, error=str(exc))

    # --- action handlers ---

    def _open_app(self, action: Action) -> str:
        app_name = action.target or "unknown"
        if self.dry_run:
            return f"[dry-run] Would open application: {app_name}"
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name.lower()])
        return f"Opened application: {app_name}"

    def _type_text(self, action: Action) -> str:
        text = action.value or ""
        if self.dry_run:
            return f"[dry-run] Would type: {text!r}"
        import pyautogui
        pyautogui.typewrite(text, interval=0.02)
        return f"Typed: {text!r}"

    def _click(self, action: Action) -> str:
        click_map = {
            ClickType.LEFT: "left",
            ClickType.RIGHT: "right",
            ClickType.MIDDLE: "middle",
        }
        btn = click_map.get(action.click_type, "left")
        clicks = 2 if action.click_type == ClickType.DOUBLE else 1
        target_desc = action.target or "current position"

        if self.dry_run:
            return f"[dry-run] Would {btn}-click ({clicks}x) on: {target_desc}"
        import pyautogui
        if action.coordinates:
            pyautogui.click(x=action.coordinates[0], y=action.coordinates[1],
                            button=btn, clicks=clicks)
        else:
            pyautogui.click(button=btn, clicks=clicks)
        return f"Clicked ({btn}, {clicks}x) on: {target_desc}"

    def _scroll(self, action: Action) -> str:
        direction = action.scroll_direction
        amount = action.scroll_amount
        if self.dry_run:
            return f"[dry-run] Would scroll {direction.value} by {amount}"
        import pyautogui
        if direction in (ScrollDirection.UP, ScrollDirection.DOWN):
            delta = amount if direction == ScrollDirection.UP else -amount
            pyautogui.scroll(delta)
        else:
            delta = -amount if direction == ScrollDirection.LEFT else amount
            pyautogui.hscroll(delta)
        return f"Scrolled {direction.value} by {amount}"

    def _navigate(self, action: Action) -> str:
        url = action.target or ""
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        if self.dry_run:
            return f"[dry-run] Would navigate to: {url}"
        import webbrowser
        webbrowser.open(url)
        return f"Navigated to: {url}"

    def _switch_window(self, action: Action) -> str:
        target = action.target or "next window"
        if self.dry_run:
            return f"[dry-run] Would switch to: {target}"
        import pyautogui
        if sys.platform == "darwin":
            pyautogui.hotkey("command", "tab")
        else:
            pyautogui.hotkey("alt", "tab")
        return f"Switched to: {target}"

    def _press_key(self, action: Action) -> str:
        key = action.value or "return"
        if self.dry_run:
            return f"[dry-run] Would press key: {key}"
        import pyautogui
        pyautogui.press(key)
        return f"Pressed key: {key}"

    def _select_text(self, action: Action) -> str:
        target = action.target or "all"
        if self.dry_run:
            return f"[dry-run] Would select: {target}"
        import pyautogui
        if target.lower() == "all":
            pyautogui.hotkey(self._mod, "a")
        return f"Selected: {target}"

    def _hotkey_action(self, action: Action) -> str:
        keys = self._hotkey_for(action.action_type)
        if not keys:
            return f"No hotkey mapped for: {action.action_type.value}"
        if self.dry_run:
            return f"[dry-run] Would press hotkey: {'+'.join(keys)}"
        import pyautogui
        pyautogui.hotkey(*keys)
        return f"Pressed hotkey: {'+'.join(keys)}"

    def _screenshot(self, action: Action) -> str:
        if self.dry_run:
            return "[dry-run] Would take a screenshot"
        import pyautogui
        img = pyautogui.screenshot()
        path = "/tmp/voicehand_screenshot.png"
        img.save(path)
        return f"Screenshot saved to {path}"

    def _media_action(self, action: Action) -> str:
        label = action.action_type.value.replace("_", " ")
        if self.dry_run:
            return f"[dry-run] Would perform media action: {label}"
        # Platform-specific media key simulation would go here
        return f"Performed media action: {label}"

    def _lock_screen(self, action: Action) -> str:
        if self.dry_run:
            return "[dry-run] Would lock screen"
        if sys.platform == "darwin":
            subprocess.run(["pmset", "displaysleepnow"], check=False)
        return "Locked screen"

    def _search(self, action: Action) -> str:
        query = action.value or ""
        if self.dry_run:
            return f"[dry-run] Would search for: {query}"
        import pyautogui
        if sys.platform == "darwin":
            pyautogui.hotkey("command", "space")
        else:
            pyautogui.hotkey("ctrl", "s")
        import time
        time.sleep(0.3)
        import pyautogui
        pyautogui.typewrite(query, interval=0.02)
        return f"Searched for: {query}"
