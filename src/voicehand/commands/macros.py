"""MacroManager - custom command sequences."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from voicehand.models import Action, ActionType, ClickType, Macro, VoiceCommand

logger = logging.getLogger(__name__)

# Built-in macros shipped with VoiceHand
DEFAULT_MACROS: list[dict] = [
    {
        "name": "morning_routine",
        "trigger_phrases": ["morning routine", "start my day", "good morning"],
        "description": "Open browser, email, and calendar to start the day",
        "actions": [
            {"action_type": "open_app", "target": "Safari"},
            {"action_type": "open_app", "target": "Mail"},
            {"action_type": "open_app", "target": "Calendar"},
        ],
    },
    {
        "name": "coding_setup",
        "trigger_phrases": ["coding setup", "start coding", "dev mode"],
        "description": "Open editor and terminal side by side",
        "actions": [
            {"action_type": "open_app", "target": "Visual Studio Code"},
            {"action_type": "open_app", "target": "Terminal"},
        ],
    },
    {
        "name": "screenshot_paste",
        "trigger_phrases": ["screenshot and paste", "capture and paste"],
        "description": "Take a screenshot then paste it",
        "actions": [
            {"action_type": "screenshot"},
            {"action_type": "paste"},
        ],
    },
    {
        "name": "select_copy",
        "trigger_phrases": ["copy all", "select and copy", "grab everything"],
        "description": "Select all text then copy",
        "actions": [
            {"action_type": "select_text", "target": "all"},
            {"action_type": "copy"},
        ],
    },
    {
        "name": "new_document",
        "trigger_phrases": ["new document", "blank document", "fresh document"],
        "description": "Create a new document via keyboard shortcut",
        "actions": [
            {"action_type": "press_key", "value": "n", "modifiers": ["command"]},
        ],
    },
]


class MacroManager:
    """Manages custom and built-in command sequences."""

    def __init__(self, macros_path: Path | None = None) -> None:
        self._macros: dict[str, Macro] = {}
        self._macros_path = macros_path or Path.home() / ".voicehand" / "macros.json"
        self._load_defaults()

    # --- public API ---

    def match(self, text: str) -> VoiceCommand | None:
        """Try to match text against registered macros.

        Returns a VoiceCommand populated from the matching macro, or None.
        """
        for macro in self._macros.values():
            if not macro.enabled:
                continue
            if macro.matches(text):
                macro.usage_count += 1
                return VoiceCommand(
                    raw_text=text,
                    actions=list(macro.actions),
                    confidence=1.0,
                    is_macro=True,
                    macro_name=macro.name,
                )
        return None

    def register(self, macro: Macro) -> None:
        """Register or overwrite a macro."""
        self._macros[macro.name] = macro
        logger.info("Registered macro: %s", macro.name)

    def unregister(self, name: str) -> bool:
        """Remove a macro by name. Returns True if found and removed."""
        if name in self._macros:
            del self._macros[name]
            return True
        return False

    def get(self, name: str) -> Macro | None:
        """Get a macro by name."""
        return self._macros.get(name)

    def list_macros(self) -> list[Macro]:
        """Return all registered macros."""
        return list(self._macros.values())

    def save(self) -> None:
        """Persist macros to disk."""
        self._macros_path.parent.mkdir(parents=True, exist_ok=True)
        data = [m.model_dump(mode="json") for m in self._macros.values()]
        self._macros_path.write_text(json.dumps(data, indent=2, default=str))
        logger.info("Saved %d macros to %s", len(data), self._macros_path)

    def load(self) -> None:
        """Load macros from disk, merging with defaults."""
        if not self._macros_path.exists():
            return
        try:
            data = json.loads(self._macros_path.read_text())
            for entry in data:
                macro = Macro(**entry)
                self._macros[macro.name] = macro
            logger.info("Loaded %d macros from %s", len(data), self._macros_path)
        except Exception:
            logger.exception("Failed to load macros from %s", self._macros_path)

    # --- internals ---

    def _load_defaults(self) -> None:
        """Load the built-in default macros."""
        for entry in DEFAULT_MACROS:
            actions = [Action(**a) for a in entry["actions"]]
            macro = Macro(
                name=entry["name"],
                trigger_phrases=entry["trigger_phrases"],
                actions=actions,
                description=entry.get("description", ""),
            )
            self._macros[macro.name] = macro
