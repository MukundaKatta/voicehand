"""VoiceListener - microphone capture with wake word detection."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

DEFAULT_WAKE_WORDS = ["hey computer", "ok computer", "voice hand", "listen up"]


@dataclass
class ListenerConfig:
    """Configuration for the voice listener."""

    wake_words: list[str] = field(default_factory=lambda: list(DEFAULT_WAKE_WORDS))
    energy_threshold: int = 300
    pause_threshold: float = 0.8
    phrase_time_limit: float = 10.0
    sample_rate: int = 16_000
    always_on: bool = False


class VoiceListener:
    """Captures audio from the microphone and detects wake words.

    The listener operates in two modes:

    * **Wake-word mode** (default): Continuously listens for a configured
      wake word. Once detected, it captures the subsequent speech and
      delivers it to the registered callback.
    * **Always-on mode**: Every detected phrase is passed to the callback
      without requiring a wake word first.

    This class wraps the ``speech_recognition`` library for audio capture
    and performs wake word detection on the transcribed text.
    """

    def __init__(self, config: ListenerConfig | None = None) -> None:
        self.config = config or ListenerConfig()
        self._callback: Callable[[str], None] | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    # --- public API ---

    def on_speech(self, callback: Callable[[str], None]) -> None:
        """Register a callback to receive transcribed speech text."""
        self._callback = callback

    def start(self) -> None:
        """Start listening in a background thread."""
        if self._running:
            logger.warning("Listener already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("VoiceListener started (always_on=%s)", self.config.always_on)

    def stop(self) -> None:
        """Stop the listener."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("VoiceListener stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    # --- wake word helpers ---

    def detect_wake_word(self, text: str) -> tuple[bool, str]:
        """Check if text starts with a wake word.

        Returns (detected, remaining_text).
        """
        text_lower = text.lower().strip()
        for wake in self.config.wake_words:
            wake_lower = wake.lower()
            if text_lower.startswith(wake_lower):
                remainder = text[len(wake_lower):].strip().lstrip(",").strip()
                return True, remainder
        return False, text

    # --- internals ---

    def _listen_loop(self) -> None:
        """Main listening loop (runs in a background thread)."""
        try:
            import speech_recognition as sr
        except ImportError:
            logger.error("speech_recognition is not installed; listener cannot start")
            self._running = False
            return

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self.config.energy_threshold
        recognizer.pause_threshold = self.config.pause_threshold

        try:
            mic = sr.Microphone(sample_rate=self.config.sample_rate)
        except Exception:
            logger.error("No microphone available")
            self._running = False
            return

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        logger.info("Listening for audio...")

        while self._running:
            try:
                with mic as source:
                    audio = recognizer.listen(
                        source,
                        phrase_time_limit=self.config.phrase_time_limit,
                    )
                text = recognizer.recognize_google(audio)
                if not text:
                    continue

                if self.config.always_on:
                    self._deliver(text)
                else:
                    detected, remainder = self.detect_wake_word(text)
                    if detected and remainder:
                        self._deliver(remainder)
                    elif detected:
                        logger.debug("Wake word detected, waiting for command...")
            except Exception:
                # Recognition errors are expected (silence, noise, etc.)
                pass

    def _deliver(self, text: str) -> None:
        """Send recognised text to the callback."""
        logger.debug("Delivering speech: %s", text)
        if self._callback:
            self._callback(text)
