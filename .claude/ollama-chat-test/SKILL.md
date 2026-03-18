---
name: ollama-chat-test
description: >
  Run and write tests for the ollama-chat CLI project. Use this skill whenever
  the user asks to run tests, verify code, check quality, write new tests, or
  after finishing any feature implementation in this project. Also triggers for
  "does this pass?", "check my code", "are tests green?", "coverage", or any
  request involving pytest, ruff, or pyrefly in the context of this codebase.
  When in doubt, use this skill — it is the single place for all quality checks
  in this project.
---

# ollama-chat Test & Quality Runner

This project lives at the current working directory. All commands use `uv run`.

## Step 1 — Run the full quality suite

Run all four checks in parallel (they are independent):

```bash
uv run pytest --tb=short -q          # tests
uv run ruff check .                   # lint
uv run ruff format --check .          # format
uv run pyrefly check .                # type checking
```

If coverage data is needed (e.g., user asks about coverage or gaps):

```bash
uv run pytest --tb=short -q --cov=chat --cov-report=term-missing
```

## Step 2 — Interpret and report results

Report in this order:

1. **Tests** — pass/fail count, any failing test names + tracebacks
2. **Ruff lint** — list of violations with file:line
3. **Ruff format** — list of files that need reformatting
4. **Pyrefly** — type errors with file:line and explanation

Keep the report concise. If everything passes, a one-liner suffices: "All checks passed (N tests, lint clean, types clean)."

## Step 3 — Suggest fixes (only on failure)

For each failure, give a specific, actionable fix. Reference the exact file and line. Don't give generic advice.

- **Test failure**: show the diff between expected and actual, then suggest the minimal fix
- **Ruff lint**: quote the rule ID and the corrected line
- **Ruff format**: run `uv run ruff format .` to auto-fix, then re-check
- **Pyrefly**: show the inferred vs. expected type; suggest the correct annotation

---

## Writing new tests

When writing or extending tests, follow these conventions exactly:

### File placement
Every `chat/foo.py` gets a matching `chat/tests/test_foo.py`. Never put tests anywhere else.

### Module structure

```python
"""Tests for chat.<module> module."""

import pytest
# other imports ...

# ---------------------------------------------------------------------------
# ClassName
# ---------------------------------------------------------------------------
class TestClassName:
    def test_does_the_specific_thing(self) -> None:
        ...
```

- Module-level docstring is required.
- One class per logical unit (mirrors the class in the source file).
- Section separator comment above each class.
- Test method names describe the behavior: `test_raises_ollama_error_on_connection_refused`, not `test_error`.

### Mocking HTTP

Use `respx` to mock `httpx` calls. Never hit a live Ollama instance.

```python
import respx
import httpx

@respx.mock
def test_chat_returns_streamed_content() -> None:
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(200, text='{"message": {"content": "hi"}}')
    )
    ...
```

For async tests:

```python
import pytest
import respx
import httpx

@pytest.mark.asyncio
@respx.mock
async def test_async_chat() -> None:
    ...
```

### Parametrize for data-driven cases

```python
@pytest.mark.parametrize("role,expected", [
    ("user", True),
    ("assistant", True),
    ("system", True),
    ("invalid", False),
])
def test_validates_message_role(role: str, expected: bool) -> None:
    ...
```

### Expected exceptions

```python
def test_raises_ollama_error_on_connection_refused() -> None:
    with pytest.raises(OllamaError, match="connection refused"):
        ...
```

### Imports

Always use absolute imports:

```python
from chat.client import OllamaClient
from chat.conversation import Conversation
```

### Coverage target

Aim for 100% on `client.py`, `conversation.py`, and `renderer.py`. Check gaps with:

```bash
uv run pytest --cov=chat --cov-report=term-missing
```

Any uncovered line in those three files is a missing test — write it.
