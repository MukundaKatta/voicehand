"""Data models for VoiceHand."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Supported action types."""

    OPEN_APP = "open_app"
    TYPE_TEXT = "type_text"
    CLICK = "click"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    SWITCH_WINDOW = "switch_window"
    PRESS_KEY = "press_key"
    SELECT_TEXT = "select_text"
    COPY = "copy"
    PASTE = "paste"
    UNDO = "undo"
    REDO = "redo"
    SAVE = "save"
    CLOSE = "close"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    SCREENSHOT = "screenshot"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    MUTE = "mute"
    PLAY_PAUSE = "play_pause"
    BRIGHTNESS_UP = "brightness_up"
    BRIGHTNESS_DOWN = "brightness_down"
    LOCK_SCREEN = "lock_screen"
    SEARCH = "search"
    NEW_TAB = "new_tab"
    CLOSE_TAB = "close_tab"
    REFRESH = "refresh"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"


class ClickType(str, Enum):
    """Mouse click types."""

    LEFT = "left"
    RIGHT = "right"
    DOUBLE = "double"
    MIDDLE = "middle"


class ScrollDirection(str, Enum):
    """Scroll directions."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class Action(BaseModel):
    """A single executable action."""

    action_type: ActionType
    target: str | None = None
    value: str | None = None
    click_type: ClickType = ClickType.LEFT
    scroll_direction: ScrollDirection = ScrollDirection.DOWN
    scroll_amount: int = 3
    coordinates: tuple[int, int] | None = None
    modifiers: list[str] = Field(default_factory=list)
    confidence: float = 1.0

    def describe(self) -> str:
        """Human-readable description of this action."""
        parts = [self.action_type.value]
        if self.target:
            parts.append(f"target={self.target}")
        if self.value:
            parts.append(f"value={self.value}")
        return " ".join(parts)


class VoiceCommand(BaseModel):
    """A parsed voice command containing one or more actions."""

    raw_text: str
    actions: list[Action]
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: float = 0.0
    context_app: str | None = None
    is_macro: bool = False
    macro_name: str | None = None

    @property
    def primary_action(self) -> Action | None:
        """Return the first action, if any."""
        return self.actions[0] if self.actions else None


class Macro(BaseModel):
    """A reusable sequence of actions triggered by a custom phrase."""

    name: str
    trigger_phrases: list[str]
    actions: list[Action]
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = 0
    enabled: bool = True

    def matches(self, text: str) -> bool:
        """Check if text matches any trigger phrase."""
        text_lower = text.lower().strip()
        return any(
            phrase.lower().strip() in text_lower for phrase in self.trigger_phrases
        )


class AppContext(BaseModel):
    """Tracks current application context for disambiguation."""

    app_name: str = ""
    window_title: str = ""
    app_type: str = ""
    url: str | None = None
    document_name: str | None = None
    last_action: Action | None = None
    history: list[str] = Field(default_factory=list, max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_browser(self) -> bool:
        """Check if current context is a browser."""
        browsers = {"safari", "chrome", "firefox", "edge", "brave", "arc", "opera"}
        return self.app_name.lower() in browsers or self.app_type == "browser"

    def is_editor(self) -> bool:
        """Check if current context is a text editor or IDE."""
        editors = {"vscode", "code", "vim", "neovim", "emacs", "sublime", "atom",
                   "intellij", "pycharm", "webstorm", "cursor", "zed"}
        return self.app_name.lower() in editors or self.app_type == "editor"

    def is_terminal(self) -> bool:
        """Check if current context is a terminal."""
        terminals = {"terminal", "iterm", "iterm2", "warp", "alacritty", "kitty",
                     "hyper", "wezterm"}
        return self.app_name.lower() in terminals or self.app_type == "terminal"
