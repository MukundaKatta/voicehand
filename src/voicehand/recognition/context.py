"""ContextTracker - maintains application context for disambiguation."""

from __future__ import annotations

import logging
import subprocess
import sys

from voicehand.models import Action, AppContext

logger = logging.getLogger(__name__)


class ContextTracker:
    """Tracks the current application context to help disambiguate commands.

    For example, "go back" means browser-back in Safari but undo in an editor.
    The tracker detects the active application and exposes rich metadata about it.
    """

    # Well-known application type categorisation
    APP_TYPES: dict[str, str] = {
        "safari": "browser",
        "chrome": "browser",
        "google chrome": "browser",
        "firefox": "browser",
        "edge": "browser",
        "brave": "browser",
        "arc": "browser",
        "opera": "browser",
        "code": "editor",
        "visual studio code": "editor",
        "cursor": "editor",
        "zed": "editor",
        "sublime text": "editor",
        "vim": "editor",
        "neovim": "editor",
        "emacs": "editor",
        "intellij idea": "editor",
        "pycharm": "editor",
        "webstorm": "editor",
        "xcode": "editor",
        "terminal": "terminal",
        "iterm2": "terminal",
        "warp": "terminal",
        "alacritty": "terminal",
        "kitty": "terminal",
        "hyper": "terminal",
        "wezterm": "terminal",
        "slack": "communication",
        "discord": "communication",
        "messages": "communication",
        "teams": "communication",
        "zoom": "communication",
        "mail": "email",
        "outlook": "email",
        "thunderbird": "email",
        "spotify": "media",
        "music": "media",
        "vlc": "media",
        "finder": "file_manager",
        "files": "file_manager",
        "notes": "notes",
        "notion": "notes",
        "obsidian": "notes",
        "pages": "document",
        "word": "document",
        "google docs": "document",
    }

    def __init__(self) -> None:
        self._context = AppContext()

    @property
    def current(self) -> AppContext:
        """Return the current application context (refreshes automatically)."""
        self._refresh()
        return self._context

    def record(self, text: str) -> None:
        """Add a command to the context history."""
        history = self._context.history
        history.append(text)
        # Keep last 50 entries
        if len(history) > 50:
            self._context.history = history[-50:]

    def update_last_action(self, action: Action) -> None:
        """Store the most recent action."""
        self._context.last_action = action

    def _refresh(self) -> None:
        """Detect the currently active application."""
        if sys.platform != "darwin":
            return

        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get name of first '
                    "application process whose frontmost is true",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            app_name = result.stdout.strip()
            if app_name:
                self._context.app_name = app_name
                self._context.app_type = self.APP_TYPES.get(app_name.lower(), "")
        except Exception:
            logger.debug("Failed to detect active application")

        # Try to get window title
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get title of first '
                    "window of first application process whose frontmost is true",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            title = result.stdout.strip()
            if title:
                self._context.window_title = title
        except Exception:
            pass
