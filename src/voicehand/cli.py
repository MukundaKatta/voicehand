"""CLI entry point for VoiceHand."""

from __future__ import annotations

import click
from rich.console import Console

from voicehand import __version__
from voicehand.commands.executor import CommandExecutor
from voicehand.commands.macros import MacroManager
from voicehand.commands.parser import CommandParser
from voicehand.recognition.context import ContextTracker
from voicehand.recognition.listener import ListenerConfig, VoiceListener
from voicehand.recognition.processor import SpeechProcessor
from voicehand.report import (
    print_command,
    print_execution_report,
    print_macros,
    print_patterns,
)

console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """VoiceHand - Voice Computer Control."""


@main.command()
@click.option("--always-on", is_flag=True, help="Skip wake word detection")
@click.option("--dry-run/--no-dry-run", default=True, help="Simulate actions without executing")
@click.option("--wake-word", multiple=True, help="Custom wake word(s)")
def listen(always_on: bool, dry_run: bool, wake_word: tuple[str, ...]) -> None:
    """Start listening for voice commands."""
    config = ListenerConfig(always_on=always_on)
    if wake_word:
        config.wake_words = list(wake_word)

    parser = CommandParser()
    macro_manager = MacroManager()
    macro_manager.load()
    context_tracker = ContextTracker()
    processor = SpeechProcessor(parser, macro_manager, context_tracker)
    executor = CommandExecutor(dry_run=dry_run)
    listener = VoiceListener(config)

    def on_speech(text: str) -> None:
        console.print(f"\n[bold cyan]Heard:[/bold cyan] {text}")
        command = processor.process(text)
        print_command(command)
        if command.actions:
            report = executor.execute(command)
            print_execution_report(report)

    listener.on_speech(on_speech)
    console.print("[bold green]VoiceHand listening...[/bold green] (Ctrl+C to stop)")
    if not always_on:
        console.print(f"Wake words: {', '.join(config.wake_words)}")

    listener.start()
    try:
        import time
        while listener.is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        console.print("\n[bold red]Stopped.[/bold red]")


@main.command()
@click.argument("text")
@click.option("--execute/--no-execute", default=False, help="Actually execute the actions")
def parse(text: str, execute: bool) -> None:
    """Parse a voice command from text (for testing)."""
    parser = CommandParser()
    macro_manager = MacroManager()
    processor = SpeechProcessor(parser, macro_manager)

    command = processor.process(text)
    print_command(command)

    if execute and command.actions:
        executor = CommandExecutor(dry_run=False)
        report = executor.execute(command)
        print_execution_report(report)


@main.command()
def patterns() -> None:
    """Show all supported voice command patterns."""
    parser = CommandParser()
    print_patterns(parser)


@main.command()
def macros() -> None:
    """List all registered macros."""
    manager = MacroManager()
    manager.load()
    print_macros(manager.list_macros())


if __name__ == "__main__":
    main()
