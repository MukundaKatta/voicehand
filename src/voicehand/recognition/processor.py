"""SpeechProcessor - converts speech text to structured VoiceCommands."""

from __future__ import annotations

import logging

from voicehand.commands.macros import MacroManager
from voicehand.commands.parser import CommandParser
from voicehand.models import AppContext, VoiceCommand
from voicehand.recognition.context import ContextTracker

logger = logging.getLogger(__name__)


class SpeechProcessor:
    """Converts raw speech text into structured VoiceCommands.

    The processing pipeline:
    1. Normalise the raw text (strip filler words, fix common mis-transcriptions).
    2. Check if the text matches a registered macro.
    3. If not a macro, run through the CommandParser.
    4. Enrich the command with the current application context.
    """

    # Common filler words / artifacts from speech recognition
    FILLER_WORDS = {
        "um", "uh", "er", "ah", "like", "you know", "basically",
        "so", "well", "actually", "literally", "please", "kindly",
    }

    # Common mis-transcription corrections
    CORRECTIONS: dict[str, str] = {
        "chrome": "Chrome",
        "safari": "Safari",
        "fire fox": "Firefox",
        "firefox": "Firefox",
        "vs code": "Visual Studio Code",
        "vscode": "Visual Studio Code",
        "v s code": "Visual Studio Code",
        "sublime": "Sublime Text",
        "i term": "iTerm2",
        "eye term": "iTerm2",
        "slack": "Slack",
        "discord": "Discord",
        "spotify": "Spotify",
        "finder": "Finder",
        "terminal": "Terminal",
        "male": "Mail",
    }

    def __init__(
        self,
        parser: CommandParser | None = None,
        macro_manager: MacroManager | None = None,
        context_tracker: ContextTracker | None = None,
    ) -> None:
        self.parser = parser or CommandParser()
        self.macro_manager = macro_manager or MacroManager()
        self.context_tracker = context_tracker or ContextTracker()

    def process(self, raw_text: str) -> VoiceCommand:
        """Process raw speech text into a structured VoiceCommand."""
        # Step 1: normalise
        cleaned = self._normalise(raw_text)
        logger.debug("Normalised: %r -> %r", raw_text, cleaned)

        # Step 2: try macros first
        macro_cmd = self.macro_manager.match(cleaned)
        if macro_cmd:
            logger.info("Matched macro: %s", macro_cmd.macro_name)
            return self._enrich(macro_cmd)

        # Step 3: parse via command parser
        command = self.parser.parse(cleaned)

        # Step 4: enrich with context
        return self._enrich(command)

    def _normalise(self, text: str) -> str:
        """Clean up speech text."""
        text = text.strip()

        # Remove filler words at the start
        words = text.split()
        while words and words[0].lower().rstrip(",") in self.FILLER_WORDS:
            words.pop(0)
        text = " ".join(words)

        # Apply corrections
        text_lower = text.lower()
        for wrong, right in self.CORRECTIONS.items():
            if wrong in text_lower:
                # Case-insensitive replacement preserving intent
                import re
                text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
                text_lower = text.lower()

        return text.strip()

    def _enrich(self, command: VoiceCommand) -> VoiceCommand:
        """Add context information to the command."""
        ctx = self.context_tracker.current
        command.context_app = ctx.app_name or None

        # Track the command in context history
        self.context_tracker.record(command.raw_text)

        # Update last action
        if command.primary_action:
            self.context_tracker.update_last_action(command.primary_action)

        return command
