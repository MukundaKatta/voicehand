"""Rich console reporting for VoiceHand."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from voicehand.commands.executor import ExecutionReport
from voicehand.commands.macros import MacroManager
from voicehand.commands.parser import CommandParser
from voicehand.models import Macro, VoiceCommand

console = Console()


def print_command(command: VoiceCommand) -> None:
    """Display a parsed voice command."""
    table = Table(title="Parsed Voice Command", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Raw text", command.raw_text)
    table.add_row("Confidence", f"{command.confidence:.0%}")
    table.add_row("Actions", str(len(command.actions)))
    table.add_row("Is macro", str(command.is_macro))
    if command.macro_name:
        table.add_row("Macro name", command.macro_name)
    if command.context_app:
        table.add_row("Context app", command.context_app)

    console.print(table)

    if command.actions:
        actions_table = Table(title="Actions", show_header=True)
        actions_table.add_column("#", style="dim")
        actions_table.add_column("Type", style="green")
        actions_table.add_column("Target", style="yellow")
        actions_table.add_column("Value", style="magenta")
        actions_table.add_column("Confidence", style="cyan")

        for i, action in enumerate(command.actions, 1):
            actions_table.add_row(
                str(i),
                action.action_type.value,
                action.target or "-",
                action.value or "-",
                f"{action.confidence:.0%}",
            )
        console.print(actions_table)


def print_execution_report(report: ExecutionReport) -> None:
    """Display an execution report."""
    style = "green" if report.all_succeeded else "red"
    console.print(Panel(report.summary, title="Execution Report", style=style))

    for result in report.results:
        icon = "[green]OK[/green]" if result.success else "[red]FAIL[/red]"
        desc = result.action.describe()
        msg = result.message or result.error or ""
        console.print(f"  {icon} {desc}: {msg}")


def print_macros(macros: list[Macro]) -> None:
    """Display registered macros."""
    table = Table(title="Registered Macros", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Triggers", style="green")
    table.add_column("Actions", style="yellow")
    table.add_column("Uses", style="magenta")
    table.add_column("Enabled", style="dim")

    for macro in macros:
        table.add_row(
            macro.name,
            ", ".join(macro.trigger_phrases),
            str(len(macro.actions)),
            str(macro.usage_count),
            "Yes" if macro.enabled else "No",
        )
    console.print(table)


def print_patterns(parser: CommandParser) -> None:
    """Display all supported voice patterns."""
    patterns = parser.get_supported_patterns()
    table = Table(title=f"Supported Voice Patterns ({len(patterns)})", show_header=True)
    table.add_column("#", style="dim")
    table.add_column("Pattern", style="cyan")
    table.add_column("Action", style="green")

    for i, desc in enumerate(patterns, 1):
        parts = desc.rsplit(" -> ", 1)
        pattern = parts[0] if len(parts) == 2 else desc
        action = parts[1] if len(parts) == 2 else ""
        table.add_row(str(i), pattern, action)
    console.print(table)
