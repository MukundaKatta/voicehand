"""Tests for VoiceListener."""

from voicehand.recognition.listener import ListenerConfig, VoiceListener


class TestWakeWordDetection:
    def test_default_wake_words(self):
        listener = VoiceListener()
        detected, remainder = listener.detect_wake_word("hey computer open chrome")
        assert detected is True
        assert remainder == "open chrome"

    def test_voice_hand_wake_word(self):
        listener = VoiceListener()
        detected, remainder = listener.detect_wake_word("voice hand scroll down")
        assert detected is True
        assert remainder == "scroll down"

    def test_no_wake_word(self):
        listener = VoiceListener()
        detected, remainder = listener.detect_wake_word("open chrome")
        assert detected is False
        assert remainder == "open chrome"

    def test_custom_wake_word(self):
        config = ListenerConfig(wake_words=["jarvis"])
        listener = VoiceListener(config)
        detected, remainder = listener.detect_wake_word("jarvis open mail")
        assert detected is True
        assert remainder == "open mail"

    def test_wake_word_only(self):
        listener = VoiceListener()
        detected, remainder = listener.detect_wake_word("hey computer")
        assert detected is True
        assert remainder == ""

    def test_wake_word_with_comma(self):
        listener = VoiceListener()
        detected, remainder = listener.detect_wake_word("hey computer, open chrome")
        assert detected is True
        assert remainder == "open chrome"


class TestListenerConfig:
    def test_defaults(self):
        config = ListenerConfig()
        assert len(config.wake_words) > 0
        assert config.energy_threshold == 300
        assert config.always_on is False

    def test_always_on(self):
        config = ListenerConfig(always_on=True)
        assert config.always_on is True
