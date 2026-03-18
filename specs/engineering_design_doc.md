---
description: This document divides prd(product requirement document) into mini phases describing the technical design and implementation details of each phase.
version: "1.0"
---

# Ollama Chat CLI — Engineering Design Document

## Phasing Strategy

Each phase is self-contained: it adds one vertical slice of functionality, ends with
passing tests, and leaves the codebase in a working state. Phases build on each other
sequentially — no phase depends on a future phase.

**Verification gate after every phase:**

```bash
uv run pytest                     # all tests pass
uv run ruff check .               # no lint errors
uv run ruff format --check .      # formatting clean
uv run pyrefly check .            # no type errors
```

No phase is complete until all four checks pass.

---

## Phase 1 — Project Skeleton & Conversation Model

**Goal:** Establish the package structure and build the data layer (no I/O, no HTTP).

**PRD coverage:** Requirements 3, 4 (conversation history).

### 1.1 Package structure

Create the directory layout from CLAUDE.md:

```
chat/
├── __init__.py
├── client.py           # empty placeholder
├── conversation.py     # ← this phase
├── repl.py             # empty placeholder
├── renderer.py         # empty placeholder
├── exceptions.py       # custom exception classes
└── tests/
    ├── __init__.py
    ├── conftest.py     # shared fixtures
    └── test_conversation.py
```

Also create:
- `conftest.py` at project root (pytest config, project-root on `sys.path`).
- `project_status.md` at project root.

### 1.2 `chat/exceptions.py`

Define the project's exception hierarchy up front so every later module can import it:

```python
class OllamaError(Exception):
    """Base exception for all Ollama client errors."""

class OllamaConnectionError(OllamaError):
    """Ollama server is unreachable."""

class OllamaModelNotFoundError(OllamaError):
    """Requested model is not available locally."""

class OllamaStreamError(OllamaError):
    """Error occurred while streaming a response."""
```

### 1.3 `chat/conversation.py`

A pure data class — no I/O, no imports beyond stdlib and typing.

```python
@dataclass
class Message:
    role: Literal["system", "user", "assistant"]
    content: str

class Conversation:
    def __init__(self) -> None: ...
    def add_message(self, role, content) -> None: ...
    def get_history(self) -> list[dict[str, str]]: ...
    def clear(self) -> None: ...
    def __len__(self) -> int: ...
```

Key behaviours:
- `get_history()` returns a list of `{"role": ..., "content": ...}` dicts (the format
  Ollama's `/api/chat` expects).
- `clear()` resets to an empty list.
- Roles are validated on `add_message` — raise `ValueError` for unknown roles.

### 1.4 Tests — `chat/tests/test_conversation.py`

| Test class | Cases |
|---|---|
| `TestMessage` | Creation with valid roles; invalid role raises `ValueError` |
| `TestConversation` | `add_message` appends correctly; `get_history` returns correct format; `clear` empties history; `__len__` matches message count; multi-turn sequence preserves order |

**Exit criteria:** `uv run pytest chat/tests/test_conversation.py` — all green.

---

## Phase 2 — Ollama HTTP Client

**Goal:** Build the HTTP client that talks to Ollama. Supports health check, model
listing, and streaming chat completions.

**PRD coverage:** Requirements 1, 2, 5-9, 20-22.

### 2.1 `chat/client.py`

```python
class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434") -> None: ...
    async def health_check(self) -> bool: ...
    async def list_models(self) -> list[dict[str, Any]]: ...
    async def chat_stream(
        self, model: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]: ...
```

**Design decisions:**

- Uses `httpx.AsyncClient` internally. Client is created in `__init__` and closed via
  an `async close()` method (or `async with` context manager via `__aenter__`/`__aexit__`).
- `health_check()` — `GET /` (Ollama returns `"Ollama is running"`). Returns `True`/`False`,
  never raises.
- `list_models()` — `GET /api/tags`. Returns the `models` list from the JSON response.
  Raises `OllamaConnectionError` if unreachable.
- `chat_stream()` — `POST /api/chat` with `{"model": ..., "messages": ..., "stream": true}`.
  Yields each `message.content` token as it arrives from the NDJSON stream. Raises
  `OllamaModelNotFoundError` if model is not found (Ollama returns 404). Raises
  `OllamaStreamError` on mid-stream failures.
- All HTTP errors are caught and wrapped in the appropriate `OllamaError` subclass —
  no `httpx` exceptions leak to callers.

### 2.2 Tests — `chat/tests/test_client.py`

Use `respx` to mock all HTTP calls. **Never hit a live Ollama instance.**

| Test class | Cases |
|---|---|
| `TestHealthCheck` | Returns `True` when Ollama responds; returns `False` on connection refused |
| `TestListModels` | Returns parsed model list; raises `OllamaConnectionError` when unreachable |
| `TestChatStream` | Yields tokens from a mocked NDJSON stream; raises `OllamaModelNotFoundError` on 404; raises `OllamaStreamError` on mid-stream disconnect; sends correct request body with model and messages |
| `TestClientLifecycle` | Context manager opens and closes `httpx.AsyncClient` properly |

**Exit criteria:** `uv run pytest chat/tests/test_client.py` — all green.

---

## Phase 3 — Renderer

**Goal:** Build the output layer that formats and displays streamed tokens and system
messages in the terminal using `rich`.

**PRD coverage:** Requirements 13, 14, 21, 22 + non-functional (error styling, no raw
tracebacks).

### 3.1 `chat/renderer.py`

```python
class Renderer:
    def __init__(self, console: Console | None = None) -> None: ...
    def welcome_banner(self, model: str) -> None: ...
    def render_streaming_response(self, token: str) -> None: ...
    def finalize_response(self, full_text: str) -> None: ...
    def render_error(self, message: str) -> None: ...
    def render_models_list(self, models: list[dict[str, Any]]) -> None: ...
    def render_help(self) -> None: ...
    def render_goodbye(self) -> None: ...
    def clear_screen(self) -> None: ...
```

**Design decisions:**

- Accepts an optional `Console` in the constructor for testability (pass a `Console`
  that writes to a `StringIO` in tests).
- `render_streaming_response()` prints a token without a newline — called once per
  streamed token. Uses `console.print(..., end="")`.
- `finalize_response()` receives the full accumulated text and re-renders it as
  proper Markdown (via `rich.markdown.Markdown`) replacing the streamed raw text.
  This gives the user instant feedback during streaming and polished formatting once
  complete.
- `welcome_banner()` shows a `rich.panel.Panel` with app name, model, and `/help` hint.
- `render_error()` styles the message in red via `rich` and writes to stderr.
- `render_models_list()` renders a `rich.table.Table` with model name and size columns.

### 3.2 Tests — `chat/tests/test_renderer.py`

Use a `Console(file=StringIO())` to capture output and assert on content.

| Test class | Cases |
|---|---|
| `TestWelcomeBanner` | Contains model name; contains `/help` hint |
| `TestStreamingResponse` | Token appears in output; no trailing newline |
| `TestFinalizeResponse` | Full text re-rendered as Markdown |
| `TestRenderError` | Error message appears; styled in red |
| `TestRenderModelsList` | Table contains model names; handles empty list |
| `TestRenderHelp` | Lists all slash commands |

**Exit criteria:** `uv run pytest chat/tests/test_renderer.py` — all green.

---

## Phase 4 — REPL, Slash Commands & CLI Entry Point

**Goal:** Wire everything together into the interactive REPL loop with slash commands
and the `typer`-based CLI entry point. After this phase the app is fully usable.

**PRD coverage:** Requirements 6, 7, 10-12, 15-19 + user flows 3.1, 3.2, 3.4.

### 4.1 `chat/repl.py`

```python
class ChatREPL:
    def __init__(
        self,
        client: OllamaClient,
        renderer: Renderer,
        model: str,
    ) -> None: ...

    async def run(self) -> None: ...
    async def handle_input(self, user_input: str) -> bool: ...
    async def handle_chat(self, user_input: str) -> None: ...
    async def handle_slash_command(self, command: str) -> bool: ...
```

**Design decisions:**

- `run()` is the main loop: show welcome banner → read input → dispatch → repeat.
  Returns on `/exit`, `quit`, or `EOFError` (Ctrl+D).
- `handle_input()` returns `True` to continue the loop, `False` to exit.
- Empty input (just Enter) is ignored — return `True` immediately.
- Input starting with `/` is routed to `handle_slash_command()`.
- Everything else is routed to `handle_chat()`.
- `handle_chat()` adds the user message to `Conversation`, calls
  `client.chat_stream()`, streams tokens through `renderer`, then adds the full
  assistant response to `Conversation`.
- Uses `asyncio` for the event loop since `httpx` and streaming are async.

**Slash command dispatch:**

| Command | Action |
|---|---|
| `/help` | `renderer.render_help()` |
| `/exit` | `renderer.render_goodbye()` → return `False` |
| `/clear` | `conversation.clear()` → `renderer.clear_screen()` |
| `/models` | `client.list_models()` → `renderer.render_models_list()` |
| `/model <name>` | Switch `self.model`, reset `conversation`, show confirmation |
| Unknown `/...` | `renderer.render_error("Unknown command. Type /help.")` |

### 4.2 `main.py`

Thin entry point — all logic lives in `chat/`:

```python
import typer
from chat.repl import ChatREPL
from chat.client import OllamaClient
from chat.renderer import Renderer

app = typer.Typer()

@app.command()
def main(
    model: str = typer.Option(None, help="Ollama model name"),
    host: str = typer.Option(None, help="Ollama server URL"),
) -> None:
    """Ollama Chat CLI — interactive terminal chat."""
    # Resolve model: --model flag > OLLAMA_MODEL env > "qwen3.5:9b"
    # Resolve host:  --host flag > OLLAMA_BASE_URL env > "http://localhost:11434"
    # Create OllamaClient, Renderer, ChatREPL
    # Run health check — exit 1 with friendly message if Ollama unreachable
    # asyncio.run(repl.run())
```

### 4.3 Tests

#### `chat/tests/test_repl.py`

Mock `OllamaClient` and `Renderer` to test REPL logic in isolation.

| Test class | Cases |
|---|---|
| `TestHandleInput` | Empty input returns `True` (ignored); slash command is dispatched; regular text goes to `handle_chat` |
| `TestHandleChat` | User message added to conversation; `chat_stream` called with correct history; assistant response added to conversation; streaming tokens passed to renderer |
| `TestSlashCommands` | `/help` calls `renderer.render_help()`; `/exit` returns `False`; `/clear` resets conversation and screen; `/models` displays model list; `/model X` switches model and resets history; unknown command shows error |
| `TestQuitAndEOF` | `quit` input exits; `EOFError` exits gracefully |

#### `chat/tests/test_main.py` (new)

Test the CLI entry point using `typer.testing.CliRunner`.

| Test class | Cases |
|---|---|
| `TestCLIFlags` | `--model` flag overrides default; `--host` flag overrides default |
| `TestEnvVarFallback` | `OLLAMA_MODEL` used when no `--model` flag; `OLLAMA_BASE_URL` used when no `--host` flag |
| `TestStartupHealthCheck` | Exit code 1 and friendly message when Ollama is unreachable |

**Exit criteria:** Full test suite passes — `uv run pytest` — all green.

---

## Phase 5 — Error Handling, Signals & Edge Cases

**Goal:** Harden the app against every edge case from PRD section 6. After this phase
the app handles all failure modes gracefully.

**PRD coverage:** All edge cases from section 6 + non-functional requirements (no raw
tracebacks, graceful degradation).

### 5.1 Signal handling in `chat/repl.py`

- **Ctrl+C during streaming:** Catch `KeyboardInterrupt` inside the streaming loop in
  `handle_chat()`. Keep partial text, add it to conversation as an incomplete assistant
  message, show a subtle "[interrupted]" indicator, return to prompt.
- **Ctrl+C at idle prompt:** Catch `KeyboardInterrupt` in the input loop. Show hint:
  *"Type /exit to quit"*. Do not exit.
- **Ctrl+D at prompt:** Catch `EOFError` from `input()`. Treat as `/exit`.

### 5.2 Mid-stream connection failure

In `client.chat_stream()`:
- If the connection drops mid-stream (`httpx.ReadError`, `httpx.RemoteProtocolError`),
  raise `OllamaStreamError` with the partial content received so far.
- In `repl.handle_chat()`, catch `OllamaStreamError`:
  - Keep the partial text.
  - Render an inline error: *"Connection lost. Your conversation is preserved — try
    sending another message."*
  - Add partial assistant message to conversation (so the user doesn't lose context).

### 5.3 Model not found

In `client.chat_stream()`:
- If Ollama returns HTTP 404, raise `OllamaModelNotFoundError(model_name)`.
- In `repl.handle_chat()`, catch it and render:
  *"Model X not found. Run `ollama pull X` first."*

### 5.4 Logging setup

In `main.py`, configure `loguru` on startup:

```python
from loguru import logger

logger.remove()  # remove default stderr handler
logger.add(
    "~/.ollama-chat/logs/chat.log",
    level=os.environ.get("LOG_LEVEL", "WARNING"),
    rotation="10 MB",
)
```

Add `logger.debug(...)` / `logger.error(...)` calls at key points in `client.py`
and `repl.py`. These go to the file — never to stdout.

### 5.5 Tests

#### Updates to `chat/tests/test_repl.py`

| Test class | New cases |
|---|---|
| `TestSignalHandling` | Ctrl+C during streaming keeps partial text and returns to prompt; Ctrl+C at idle shows hint and continues; Ctrl+D exits gracefully |
| `TestMidStreamFailure` | `OllamaStreamError` shows inline error; partial text preserved in conversation |
| `TestModelNotFound` | `OllamaModelNotFoundError` shows friendly message with model name |

#### Updates to `chat/tests/test_client.py`

| Test class | New cases |
|---|---|
| `TestChatStream` | Mid-stream `httpx.ReadError` raises `OllamaStreamError`; HTTP 404 raises `OllamaModelNotFoundError` |

**Exit criteria:** Full test suite passes — `uv run pytest` — all green. Manual smoke
test: start the app, chat, try Ctrl+C during streaming, try a non-existent model, kill
Ollama mid-conversation.

---

## Phase Summary

| Phase | Modules touched | PRD reqs | Key deliverable |
|---|---|---|---|
| 1 | `conversation.py`, `exceptions.py` | 3, 4 | Data layer + project skeleton |
| 2 | `client.py` | 1, 2, 5-9, 20-22 | HTTP client with streaming |
| 3 | `renderer.py` | 13, 14, 21, 22 | Rich terminal output |
| 4 | `repl.py`, `main.py` | 6, 7, 10-12, 15-19 | Working CLI app |
| 5 | `repl.py`, `client.py`, `main.py` | All edge cases (§6) | Hardened error handling |

Each phase ends with all tests green and all linting/formatting/type checks passing.
