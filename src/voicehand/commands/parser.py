"""CommandParser - extracts actions from voice text."""

from __future__ import annotations

import re
from typing import Any

from voicehand.models import (
    Action,
    ActionType,
    ClickType,
    ScrollDirection,
    VoiceCommand,
)

# 50+ voice command patterns organized by action type
COMMAND_PATTERNS: list[dict[str, Any]] = [
    # --- open_app patterns (1-8) ---
    {"pattern": r"\bopen\s+(.+)", "action": ActionType.OPEN_APP, "target_group": 1},
    {"pattern": r"\blaunch\s+(.+)", "action": ActionType.OPEN_APP, "target_group": 1},
    {"pattern": r"\bstart\s+(.+)", "action": ActionType.OPEN_APP, "target_group": 1},
    {"pattern": r"\brun\s+(.+)", "action": ActionType.OPEN_APP, "target_group": 1},
    {"pattern": r"\bswitch\s+to\s+(.+)", "action": ActionType.SWITCH_WINDOW, "target_group": 1},
    {"pattern": r"\bgo\s+to\s+(.+)", "action": ActionType.NAVIGATE, "target_group": 1},
    {"pattern": r"\bnavigate\s+to\s+(.+)", "action": ActionType.NAVIGATE, "target_group": 1},
    {"pattern": r"\bbrowse\s+to\s+(.+)", "action": ActionType.NAVIGATE, "target_group": 1},

    # --- type_text patterns (9-16) ---
    {"pattern": r"\btype\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r"\bwrite\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r"\benter\s+text\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r"\binput\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r'\bsay\s+"([^"]+)"', "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r"\bdictate\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r"\binsert\s+text\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},
    {"pattern": r"\bfill\s+in\s+(.+)", "action": ActionType.TYPE_TEXT, "value_group": 1},

    # --- click patterns (17-23) ---
    {"pattern": r"\bclick\s+on\s+(.+)", "action": ActionType.CLICK, "target_group": 1},
    {"pattern": r"\bclick\s+(.+)", "action": ActionType.CLICK, "target_group": 1},
    {"pattern": r"\bpress\s+(.+)\s+button", "action": ActionType.CLICK, "target_group": 1},
    {"pattern": r"\bright\s+click\s+(?:on\s+)?(.+)", "action": ActionType.CLICK, "target_group": 1, "click_type": ClickType.RIGHT},
    {"pattern": r"\bdouble\s+click\s+(?:on\s+)?(.+)", "action": ActionType.CLICK, "target_group": 1, "click_type": ClickType.DOUBLE},
    {"pattern": r"\btap\s+(?:on\s+)?(.+)", "action": ActionType.CLICK, "target_group": 1},
    {"pattern": r"\bselect\s+(.+)", "action": ActionType.SELECT_TEXT, "target_group": 1},

    # --- scroll patterns (24-29) ---
    {"pattern": r"\bscroll\s+up(?:\s+(\d+))?", "action": ActionType.SCROLL, "scroll_dir": ScrollDirection.UP, "amount_group": 1},
    {"pattern": r"\bscroll\s+down(?:\s+(\d+))?", "action": ActionType.SCROLL, "scroll_dir": ScrollDirection.DOWN, "amount_group": 1},
    {"pattern": r"\bscroll\s+left(?:\s+(\d+))?", "action": ActionType.SCROLL, "scroll_dir": ScrollDirection.LEFT, "amount_group": 1},
    {"pattern": r"\bscroll\s+right(?:\s+(\d+))?", "action": ActionType.SCROLL, "scroll_dir": ScrollDirection.RIGHT, "amount_group": 1},
    {"pattern": r"\bpage\s+up", "action": ActionType.SCROLL, "scroll_dir": ScrollDirection.UP, "fixed_amount": 10},
    {"pattern": r"\bpage\s+down", "action": ActionType.SCROLL, "scroll_dir": ScrollDirection.DOWN, "fixed_amount": 10},

    # --- keyboard shortcut patterns (30-40) ---
    {"pattern": r"\bcopy\s*(?:that|this|it)?$", "action": ActionType.COPY},
    {"pattern": r"\bpaste\s*(?:that|this|it)?$", "action": ActionType.PASTE},
    {"pattern": r"\bundo\s*(?:that|this|it)?$", "action": ActionType.UNDO},
    {"pattern": r"\bredo\s*(?:that|this|it)?$", "action": ActionType.REDO},
    {"pattern": r"\bsave\s*(?:file|document|that|this|it)?$", "action": ActionType.SAVE},
    {"pattern": r"\bclose\s+(?:the\s+)?window", "action": ActionType.CLOSE},
    {"pattern": r"\bclose\s+(?:the\s+)?tab", "action": ActionType.CLOSE_TAB},
    {"pattern": r"\bclose\s+(?:the\s+)?app(?:lication)?", "action": ActionType.CLOSE},
    {"pattern": r"\bminimize(?:\s+(?:the\s+)?window)?", "action": ActionType.MINIMIZE},
    {"pattern": r"\bmaximize(?:\s+(?:the\s+)?window)?", "action": ActionType.MAXIMIZE},
    {"pattern": r"\bfull\s*screen", "action": ActionType.MAXIMIZE},

    # --- browser patterns (41-47) ---
    {"pattern": r"\bnew\s+tab", "action": ActionType.NEW_TAB},
    {"pattern": r"\bopen\s+(?:a\s+)?new\s+tab", "action": ActionType.NEW_TAB},
    {"pattern": r"\brefresh(?:\s+(?:the\s+)?page)?", "action": ActionType.REFRESH},
    {"pattern": r"\breload(?:\s+(?:the\s+)?page)?", "action": ActionType.REFRESH},
    {"pattern": r"\bgo\s+back", "action": ActionType.GO_BACK},
    {"pattern": r"\bgo\s+forward", "action": ActionType.GO_FORWARD},
    {"pattern": r"\bsearch\s+(?:for\s+)?(.+)", "action": ActionType.SEARCH, "value_group": 1},

    # --- system patterns (48-55) ---
    {"pattern": r"\bscreenshot", "action": ActionType.SCREENSHOT},
    {"pattern": r"\btake\s+(?:a\s+)?screenshot", "action": ActionType.SCREENSHOT},
    {"pattern": r"\bcapture\s+screen", "action": ActionType.SCREENSHOT},
    {"pattern": r"\bvolume\s+up", "action": ActionType.VOLUME_UP},
    {"pattern": r"\bvolume\s+down", "action": ActionType.VOLUME_DOWN},
    {"pattern": r"\bmute(?:\s+(?:the\s+)?(?:sound|audio|volume))?", "action": ActionType.MUTE},
    {"pattern": r"\bplay\b|\bpause\b", "action": ActionType.PLAY_PAUSE},
    {"pattern": r"\block\s+(?:the\s+)?screen", "action": ActionType.LOCK_SCREEN},

    # --- key press patterns (56-58) ---
    {"pattern": r"\bpress\s+(?:the\s+)?escape(?:\s+key)?", "action": ActionType.PRESS_KEY, "fixed_value": "escape"},
    {"pattern": r"\bpress\s+(?:the\s+)?enter(?:\s+key)?", "action": ActionType.PRESS_KEY, "fixed_value": "return"},
    {"pattern": r"\bpress\s+(?:the\s+)?tab(?:\s+key)?", "action": ActionType.PRESS_KEY, "fixed_value": "tab"},
]


class CommandParser:
    """Extracts actions from voice text using pattern matching."""

    def __init__(self) -> None:
        self._compiled_patterns: list[tuple[re.Pattern[str], dict[str, Any]]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile all regex patterns."""
        for entry in COMMAND_PATTERNS:
            pattern = re.compile(entry["pattern"], re.IGNORECASE)
            config = {k: v for k, v in entry.items() if k != "pattern"}
            self._compiled_patterns.append((pattern, config))

    def parse(self, text: str) -> VoiceCommand:
        """Parse voice text into a VoiceCommand with extracted actions."""
        text = text.strip()
        if not text:
            return VoiceCommand(raw_text=text, actions=[], confidence=0.0)

        # Try compound commands separated by "and then", "then", "and"
        segments = re.split(r"\b(?:and\s+then|then|after\s+that)\b", text, flags=re.IGNORECASE)
        if len(segments) == 1:
            segments = [text]

        actions: list[Action] = []
        total_confidence = 0.0

        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            action = self._parse_single(segment)
            if action:
                actions.append(action)
                total_confidence += action.confidence

        avg_confidence = total_confidence / len(actions) if actions else 0.0

        return VoiceCommand(
            raw_text=text,
            actions=actions,
            confidence=round(avg_confidence, 2),
        )

    def _parse_single(self, text: str) -> Action | None:
        """Parse a single command segment into an Action."""
        text = text.strip().rstrip(".")

        best_action: Action | None = None
        best_match_len = 0

        for pattern, config in self._compiled_patterns:
            match = pattern.search(text)
            if not match:
                continue
            match_len = match.end() - match.start()
            if match_len <= best_match_len:
                continue

            best_match_len = match_len
            action_type: ActionType = config["action"]

            target = None
            value = None
            click_type = config.get("click_type", ClickType.LEFT)
            scroll_direction = config.get("scroll_dir", ScrollDirection.DOWN)
            scroll_amount = 3

            if "target_group" in config:
                group_idx = config["target_group"]
                target = match.group(group_idx).strip() if match.lastindex and match.lastindex >= group_idx else None

            if "value_group" in config:
                group_idx = config["value_group"]
                value = match.group(group_idx).strip() if match.lastindex and match.lastindex >= group_idx else None

            if "fixed_value" in config:
                value = config["fixed_value"]

            if "amount_group" in config and match.lastindex:
                group_idx = config["amount_group"]
                try:
                    scroll_amount = int(match.group(group_idx))
                except (TypeError, ValueError):
                    scroll_amount = config.get("fixed_amount", 3)
            elif "fixed_amount" in config:
                scroll_amount = config["fixed_amount"]

            confidence = min(1.0, match_len / max(len(text), 1))
            confidence = max(0.3, confidence)

            best_action = Action(
                action_type=action_type,
                target=target,
                value=value,
                click_type=click_type,
                scroll_direction=scroll_direction,
                scroll_amount=scroll_amount,
                confidence=round(confidence, 2),
            )

        return best_action

    def get_supported_patterns(self) -> list[str]:
        """Return human-readable descriptions of all supported patterns."""
        descriptions = []
        for entry in COMMAND_PATTERNS:
            pattern_str = entry["pattern"]
            action = entry["action"]
            readable = pattern_str.replace(r"\b", "").replace(r"\s+", " ")
            readable = re.sub(r"\(.*?\)", "<...>", readable)
            descriptions.append(f"{readable} -> {action.value}")
        return descriptions
