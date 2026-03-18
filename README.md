# Ollama Chat CLI

A terminal-based interactive chat application for developers who run [Ollama](https://ollama.com) locally. Stream multi-turn conversations with any locally-installed LLM — no browser, no cloud, just a fast prompt in your terminal.

## Features

- **Streaming responses** — tokens appear on screen as they arrive, rendered as Markdown
- **Multi-turn context** — full conversation history maintained across turns
- **Model switching** — list and swap models mid-session without restarting
- **Graceful error handling** — no raw tracebacks; friendly messages for every failure mode
- **Signal-safe** — Ctrl+C cancels streaming and returns to the prompt; Ctrl+D exits cleanly
- **Fully local** — zero network calls outside `localhost`

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) running locally

```bash
# Start the Ollama server
ollama serve

# Pull the default model
ollama pull llama3.2
```

## Installation

```bash
git clone <repo-url>
cd claude_code
uv sync
```

## Usage

```bash
# Start with the default model (llama3.2)
uv run python main.py

# Use a specific model
uv run python main.py --model mistral

# Point at a non-default Ollama host
uv run python main.py --host http://192.168.1.10:11434
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | Model to use (overridden by `--model` flag) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (overridden by `--host` flag) |
| `LOG_LEVEL` | `WARNING` | Log level written to `logs/chat.log` (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Slash commands

| Command | Description |
|---|---|
| `/help` | Show all available commands |
| `/models` | List locally-available models with sizes |
| `/model <name>` | Switch to a different model (resets conversation history) |
| `/clear` | Clear conversation history and terminal screen |
| `/exit` | Exit the app |

**Keyboard shortcuts**

| Key | Action |
|---|---|
| Ctrl+C | Cancel in-progress streaming; keep partial response; return to prompt |
| Ctrl+D | Exit (same as `/exit`) |
| `quit` | Exit (same as `/exit`) |

## Project structure

```
.
├── chat/
│   ├── client.py        # Ollama HTTP client (httpx, NDJSON streaming)
│   ├── conversation.py  # In-memory conversation state and history
│   ├── renderer.py      # Rich terminal output (Markdown, tables, panels)
│   ├── repl.py          # REPL loop, slash command dispatch, signal handling
│   ├── exceptions.py    # OllamaError exception hierarchy
│   └── tests/           # pytest test suite (88 tests)
├── specs/
│   ├── prd.md                     # Product requirements
│   └── engineering_design_doc.md  # Phase-wise technical design
├── main.py              # CLI entry point (typer)
├── pyproject.toml
├── project_status.md    # Implementation progress tracker
└── logs/chat.log        # Runtime log (auto-created, gitignored)
```

## Development

```bash
# Run all tests
uv run pytest

# Run tests for a specific module
uv run pytest chat/tests/test_client.py

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run pyrefly check .
```

## Tech stack

| Library | Role |
|---|---|
| `httpx` | Async HTTP client with streaming support |
| `rich` | Markdown rendering, panels, and tables in the terminal |
| `typer` | CLI flag and argument parsing |
| `loguru` | File-based structured logging |
| `pytest` + `pytest-asyncio` | Test runner with async support |
| `respx` | Mock `httpx` calls in tests |
| `ruff` | Linting and formatting |
| `pyrefly` | Type checking |

## Error scenarios

| Scenario | Behavior |
|---|---|
| Ollama not running at startup | Friendly error message, exit code 1 |
| Connection drops mid-stream | Partial response kept, error shown inline, prompt returns |
| Model not downloaded locally | `"Model X not found. Run ollama pull X first."` |
| Empty input | Silently ignored, prompt re-shown |
| Ctrl+C during streaming | Response cancelled, partial text preserved in history |
| Ctrl+C at idle prompt | Shows `"Type /exit to quit."`, does not exit |
