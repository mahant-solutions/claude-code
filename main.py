"""Ollama Chat CLI — thin entry point."""

import asyncio
import os

import typer
from loguru import logger

from chat.client import OllamaClient
from chat.renderer import Renderer
from chat.repl import ChatREPL

app = typer.Typer()

_DEFAULT_MODEL = "qwen2.5vl:3b"
_DEFAULT_HOST = "http://localhost:11434"


@app.command()
def main(
    model: str | None = typer.Option(None, help="Ollama model name"),
    host: str | None = typer.Option(None, help="Ollama server URL"),
) -> None:
    """Ollama Chat CLI — interactive terminal chat."""
    _configure_logging()

    resolved_model = model or os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)
    resolved_host = host or os.environ.get("OLLAMA_BASE_URL", _DEFAULT_HOST)

    async def _run() -> None:
        async with OllamaClient(resolved_host) as client:
            healthy = await client.health_check()
            if not healthy:
                renderer = Renderer()
                renderer.render_error(
                    f"Cannot connect to Ollama at {resolved_host}. "
                    "Is Ollama running? Try: ollama serve"
                )
                raise typer.Exit(code=1)

            renderer = Renderer()
            repl = ChatREPL(client=client, renderer=renderer, model=resolved_model)
            await repl.run()

    asyncio.run(_run())


def _configure_logging() -> None:
    """Configure loguru to write to a rotating log file inside the project."""
    logger.remove()
    log_path = os.path.join(os.path.dirname(__file__), "logs", "chat.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger.add(
        log_path,
        level=os.environ.get("LOG_LEVEL", "WARNING"),
        rotation="10 MB",
    )


if __name__ == "__main__":
    app()
