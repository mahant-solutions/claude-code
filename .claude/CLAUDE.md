# CLAUDE.md — ollama-chat CLI

## Project Overview

A terminal-based interactive chat application written in Python.
Communicates with a locally-running [Ollama](https://ollama.com) instance via its HTTP API.
Supports multi-turn conversations, model selection, and a clean REPL-style interface.

## Package Structure

```
.
├── chat/                   # Core application package
│   ├── __init__.py
│   ├── client.py           # Ollama HTTP client (thin wrapper around the API)
│   ├── conversation.py     # Conversation state & history management
│   ├── repl.py             # REPL / CLI entry-point loop
│   ├── renderer.py         # Output formatting & streaming renderer
│   └── tests/
│       ├── test_client.py
│       ├── test_conversation.py
│       ├── test_repl.py
│       └── test_renderer.py
├── specs/
│   ├── prd.md                  # Product requirements (the "what" and "why")
│   └── engineering_design_doc.md  # Phase-wise technical implementation detail
├── main.py                 # Thin entry-point — calls chat.repl.run()
├── pyproject.toml
└── project_status.md       # Track implementation progress per phase
```

**Rule:** Keep each concern in its own module. `client.py` knows nothing about rendering;
`repl.py` knows nothing about HTTP. Never put cross-module logic in `main.py`.

## Specs

Before implementing any feature, consult the relevant specs:

- **`specs/prd.md`** — Product requirements (the "what" and "why").
- **`specs/engineering_design_doc.md`** — Phase-wise technical implementation detail.
- **`project_status.md`** — Track implementation progress here against the phases in `engineering_design_doc.md`.

**Rule:** Specs are the single source of truth. If implementation requires a deviation, update the spec first, then the code.

## Workflow

1. **Plan first.** Before writing code, outline the steps. Ask for clarification on ambiguous trade-offs.
2. **One step at a time.** Implement and verify each step by writing relevant tests if not already, before moving on.
3. **Verify after every step.** Use the `/ollama-chat-test` skill — it runs pytest, ruff, and pyrefly in one go and reports results clearly.
4. **Never leave the codebase broken** between steps.
5. **Bump spec versions after every spec change.** After any modification to the codebase that requires a plan change, increment the minor version (e.g. `1.1` → `1.2`) in both `specs/prd.md` and `specs/engineering_design_doc.md`. Do this automatically — never wait to be asked.
6. **Ping me if CLAUDE.md needs to be updated.** If during code modifications/planning there's anything worth adding/updating/removing from CLAUDE.md, propose it with a summarized pros & cons.

## Ollama Integration

- **Base URL:** `http://localhost:11434` (configurable via `OLLAMA_BASE_URL` env var).
- **Key endpoints used:**
  | Endpoint | Purpose |
  |---|---|
  | `POST /api/chat` | Multi-turn chat with streaming support |
  | `GET /api/tags` | List locally available models |
  | `POST /api/pull` | Pull a model by name |
- Use `httpx` with `stream=True` for streaming responses — never buffer the full reply.
- Always surface a clear error when Ollama is not reachable (connection refused → friendly message, not a traceback).
- Never hardcode the model name — default to `llama3.2` but allow override via `--model` flag and `OLLAMA_MODEL` env var.

## Tooling

| Tool     | Purpose                        |
|----------|--------------------------------|
| `uv`     | Dependency management          |
| `httpx`  | Async-capable HTTP client      |
| `rich`   | Terminal rendering & Markdown  |
| `typer`  | CLI argument parsing           |
| `ruff`   | Linting and formatting         |
| `pyrefly`| Type checking                  |
| `pytest` | Testing (`pytest-asyncio`)     |

```bash
uv run python main.py                  # start the chat REPL
uv run python main.py --model mistral  # use a specific model
uv run pytest                          # run all tests
uv run pytest chat/tests/              # run specific module tests
uv run ruff check .                    # lint
uv run ruff format --check .           # format check
uv run pyrefly check .                 # type checking
```

- Use context7 MCP for up-to-date documentation on `httpx`, `rich`, `typer`, or any other library.

## Coding Standards

### SOLID Principles

- **Single Responsibility:** `client.py` — HTTP only. `conversation.py` — history only. `renderer.py` — display only. `repl.py` — user I/O loop only. Never mix concerns.
- **Open/Closed:** New capabilities (e.g. system-prompt support, tool calls) get their own module or mixin. Never add `if feature == ...` conditionals inside existing modules.
- **Liskov Substitution:** All subclasses must match their base interface exactly — same signatures, return types, and exception semantics.
- **Interface Segregation:** Keep base classes and protocols minimal. Don't force methods that subclasses don't need.
- **Dependency Inversion:** `repl.py` depends on the `OllamaClient` protocol, not a concrete class. Pass dependencies in rather than importing them at call sites.

### Type Annotations

- All function signatures must have full type annotations (parameters and return types).
- Modern union syntax: `str | None`, `int | float` (not `Optional`, `Union`).
- Lowercase generics: `list[str]`, `dict[str, Any]`.
- Docstrings: Google-style with Args/Returns/Raises for all public functions.

### Error Handling

- Use `loguru` for logging — never `print()` or stdlib `logging`.
- User-facing errors go through `renderer.py` (styled with `rich`) — never raw tracebacks in the terminal.
- Raise `ValueError` / `TypeError` with descriptive messages internally.
- Wrap all Ollama HTTP calls in a dedicated exception (`OllamaError`) so callers don't leak `httpx` internals.

### General Rules

- Always use absolute imports.
- All CLI commands are defined with `typer` — no raw `argparse` or `sys.argv` parsing.
- `conversation.py` is the single owner of chat history — no other module appends to it directly.
- Never commit secrets or credentials — use environment variables.
- Streaming output must flush incrementally; never wait for the full response before printing.

## Testing Conventions

- **Mirror structure:** every `chat/foo.py` has a corresponding `chat/tests/test_foo.py`.
- **Group tests into classes:** `TestOllamaClient`, `TestConversation`, etc.
- **Section separators** between test classes:
  ```python
  # ---------------------------------------------------------------------------
  # OllamaClient
  # ---------------------------------------------------------------------------
  class TestOllamaClient:
  ```
- **One behavior per test**, named descriptively: `test_raises_ollama_error_on_connection_refused`.
- Use `@pytest.mark.parametrize` for data-driven cases.
- Use `pytest.raises` for expected exceptions.
- Use `respx` (or `pytest-httpx`) to mock `httpx` calls — never hit a live Ollama instance in tests.
- Absolute imports: `from chat.client import OllamaClient`.
- Add module-level docstring: `"""Tests for chat.client module."""`
- Target **100% coverage** on business logic (`client.py`, `conversation.py`, `renderer.py`).
