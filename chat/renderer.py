"""Output formatting and streaming renderer using Rich."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class Renderer:
    """Formats and displays streamed tokens and system messages in the terminal.

    Args:
        console: Optional Rich Console instance. A default stderr-aware Console
            is created when not provided.
    """

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def welcome_banner(self, model: str) -> None:
        """Display the welcome banner with model name and help hint.

        Args:
            model: The active model name to display.
        """
        self._console.print(
            Panel(
                f"[bold]Ollama Chat CLI[/bold]\n"
                f"Model: [cyan]{model}[/cyan]\n"
                f"Type [green]/help[/green] for available commands.",
                title="Welcome",
                expand=False,
            )
        )

    def render_assistant_label(self) -> None:
        """Print the 'Assistant:' label before a streamed response begins."""
        self._console.print("\n[bold blue]Assistant[/bold blue]: ", end="")

    def render_streaming_response(self, token: str) -> None:
        """Print a single streamed token without a trailing newline.

        Args:
            token: The token string to display.
        """
        self._console.print(token, end="", highlight=False)

    def finalize_response(self, full_text: str) -> None:  # noqa: ARG002
        """Terminate the streamed output with a trailing newline.

        Called once streaming is complete. Does not re-render the text —
        streaming already displayed it incrementally.

        Args:
            full_text: Unused; kept for interface consistency.
        """
        self._console.print()

    def render_error(self, message: str) -> None:
        """Display an error message styled in red.

        Args:
            message: The error message to display.
        """
        self._console.print(f"[bold red]Error:[/bold red] {message}")

    def render_models_list(self, models: list[dict[str, Any]]) -> None:
        """Render a table of available Ollama models.

        Args:
            models: List of model dicts from the Ollama /api/tags endpoint.
        """
        table = Table(title="Available Models", show_lines=True)
        table.add_column("Name", style="cyan")
        table.add_column("Size", justify="right")

        if not models:
            self._console.print("[dim]No models available.[/dim]")
            return

        for model in models:
            name: str = model.get("name", "unknown")
            size_bytes: int = model.get("size", 0)
            size_str = _format_size(size_bytes)
            table.add_row(name, size_str)

        self._console.print(table)

    def render_help(self) -> None:
        """Display all available slash commands."""
        table = Table(title="Commands", show_lines=True)
        table.add_column("Command", style="green")
        table.add_column("Description")

        commands = [
            ("/help", "Show this help message"),
            ("/exit", "Exit the chat"),
            ("/clear", "Clear conversation history and screen"),
            ("/models", "List locally available models"),
            ("/model <name>", "Switch to a different model"),
        ]
        for cmd, desc in commands:
            table.add_row(cmd, desc)

        self._console.print(table)

    def render_info(self, message: str) -> None:
        """Display a general informational message.

        Args:
            message: The info message to display.
        """
        self._console.print(f"[green]{message}[/green]")

    def render_goodbye(self) -> None:
        """Display a farewell message."""
        self._console.print("[dim]Goodbye![/dim]")

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        self._console.clear()


def _format_size(size_bytes: int) -> str:
    """Convert a byte count to a human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string (e.g. "3.8 GB").
    """
    if size_bytes == 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} PB"
