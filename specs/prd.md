---
description: This document explains how the product is supposed to work in plain English
version: "1.0"
---

# Ollama Chat CLI — Product Requirements Document

## 1. Overview

Ollama Chat CLI is a terminal-based interactive chat application for developers who run
Ollama locally. It provides a clean, REPL-style interface for multi-turn conversations
with any locally-installed LLM — no browser, no cloud dependency, just a fast prompt in
your terminal.

## 2. Goals and Non-Goals

### Goals

- Provide a responsive, streaming multi-turn chat experience in the terminal.
- Let users pick any locally-available Ollama model at startup or mid-session.
- Render model responses as formatted Markdown (code blocks, bold, lists).
- Handle all errors gracefully — the user should never see a raw traceback.
- Stay entirely local — zero network calls outside `localhost`.

### Non-Goals

- No graphical UI (web, Electron, TUI framework like Textual). This is a REPL.
- No cloud LLM support (OpenAI, Anthropic, etc.). Ollama-only.
- No persistent chat history to disk (deferred to a future phase).
- No plugin or extension system.
- No multi-user or server mode.

## 3. User Flows

### 3.1 Start a chat session

The user runs `uv run python main.py` (optionally with `--model mistral`). The app
connects to the local Ollama server, verifies it is reachable, prints a welcome banner
showing the active model name, and presents a prompt (`> `). The user types a message
and presses Enter. The model's response streams token-by-token into the terminal,
rendered as Markdown. The prompt reappears and the conversation continues with full
context from previous turns.

### 3.2 List and switch models

The user types `/models` during a session. The app calls `GET /api/tags` and displays a
numbered list of locally-available models with their sizes. The user can then type
`/model <name>` to switch. The conversation history resets on model switch and a
confirmation message is shown.

### 3.3 Handle errors

If Ollama is not running when the app starts, the user sees a friendly message:
*"Could not connect to Ollama at http://localhost:11434. Is it running?"* and the app
exits with code 1. If the connection drops mid-stream, the partial response is kept and
an error line is appended: *"Connection lost. Your conversation is preserved — try
sending another message."*

### 3.4 Exit the session

The user types `/exit`, `quit`, or presses Ctrl+D. The app prints a goodbye message and
exits cleanly with code 0. Pressing Ctrl+C during streaming cancels the current response
(partial text is kept) and returns to the prompt — it does not kill the app.

## 4. Functional Requirements

### Chat Core

1. Send user messages to Ollama via `POST /api/chat` with the full conversation history.
2. Stream responses token-by-token — display each token as soon as it arrives.
3. Maintain an in-memory conversation history (list of `{role, content}` dicts).
4. Support the `system`, `user`, and `assistant` roles in the history.

### Model Management

5. Default model: `qwen3.5:9b`.
6. Override via `--model` CLI flag (highest priority).
7. Override via `OLLAMA_MODEL` environment variable (second priority).
8. `/models` slash command lists locally-available models from `GET /api/tags`.
9. `/model <name>` switches the active model and resets conversation history.

### CLI Interface

10. Entry point via `typer` with `--model` and `--host` optional flags.
11. `--host` overrides the default base URL (`http://localhost:11434`), also configurable
    via `OLLAMA_BASE_URL` env var.
12. REPL loop with a `> ` prompt character.
13. Responses rendered as Markdown using `rich` (code blocks with syntax highlighting,
    bold, italics, lists, headings).
14. Welcome banner on startup showing: app name, active model, and a hint about `/help`.

### Slash Commands

15. `/help` — Show available commands.
16. `/exit` — Exit the application.
17. `/clear` — Clear conversation history and terminal screen.
18. `/models` — List locally-available models.
19. `/model <name>` — Switch to a different model (resets history).

### Streaming

20. Use `httpx` with `stream=True` to consume Ollama's streaming response.
21. Flush each token to the terminal immediately — no buffering until completion.
22. Show a spinner or subtle indicator while waiting for the first token.

## 5. Non-Functional Requirements

- **Startup speed:** App should reach the prompt in under 1 second (excluding Ollama's
  first model load time).
- **Streaming latency:** Tokens must appear on screen within 50ms of receipt from Ollama.
- **Error messages:** Always human-readable, styled with `rich`, and written to stderr.
  Never expose raw tracebacks to the user.
- **Logging:** Use `loguru`, log to a file (`~/.ollama-chat/logs/`), not to stdout.
  Configurable via `LOG_LEVEL` env var (default: `WARNING`).
- **Compatibility:** Python 3.12+. macOS and Linux. Any terminal that supports ANSI
  escape codes (virtually all modern terminals).

## 6. Edge Cases and Error Scenarios

| Scenario | Expected Behavior |
|---|---|
| Ollama not running at startup | Friendly error message, exit code 1 |
| Ollama goes down mid-stream | Keep partial response, show error inline, return to prompt |
| User selects a model not downloaded locally | Show error: "Model X not found. Run `ollama pull X` first." |
| User sends empty input (just Enter) | Ignore silently, re-show prompt |
| Very long user input | Send as-is — Ollama handles its own context limits |
| Ctrl+C during streaming | Cancel current response, keep partial text, return to prompt |
| Ctrl+C at idle prompt | Ignore (or show hint: "Type /exit to quit") |
| Ctrl+D at prompt | Exit gracefully, same as `/exit` |
| Terminal resize during output | `rich` handles reflow automatically |

## 7. Tech Stack

| Library | Role |
|---|---|
| `httpx` | Async HTTP client with streaming support for Ollama API |
| `rich` | Markdown rendering, panels, syntax highlighting in the terminal |
| `typer` | CLI argument and flag parsing |
| `loguru` | Structured file-based logging |
| `pytest` + `pytest-asyncio` | Test runner with async support |
| `respx` | Mock `httpx` calls in tests |
| `ruff` | Linting and formatting |
| `pyrefly` | Type checking |

## 8. Future Considerations

- **Chat history persistence** — save/load sessions to `~/.ollama-chat/history/`.
- **System prompt customization** — `--system` flag or a config file.
- **Model pulling** — integrate `POST /api/pull` so users can download models without
  leaving the app.
- **Configuration file** — TOML-based config at `~/.ollama-chat/config.toml`.
- **Conversation export** — dump the current session as Markdown or JSON.
- **Multi-modal support** — attach images to messages for vision models.
- **Custom slash commands** — let users register their own via config.
