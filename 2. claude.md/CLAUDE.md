# Weather CLI Demo

This project demonstrates how CLAUDE.md shapes Claude's behavior.

## Tech Stack
- Python 3.12+
- uv for dependency management
- httpx for HTTP requests
- Environment variables from `.env.example` in project root

## Commands
- Install: `uv sync`
- Run: `uv run python main.py <city>`
- Test: `uv run pytest`

## Rules
- All API keys must come from environment variables, never hardcoded
- Use `pydantic` models for API responses — no raw dicts
- Use `pathlib.Path` for file operations
- Use `logging` instead of `print()` for debug info
- Keep functions under 20 lines
- Type hints on all function signatures
- Handle API errors by returning `None`, not raising exceptions

## Design Best Practices
- Separate I/O (API calls, file reads) from pure logic (formatting, parsing)
- Use constants for magic values — no unnamed strings or numbers inline
- Use `httpx.Client` with `timeout` instead of bare `httpx.get()` for production-ready requests
- Configure logging format at the application entry point, not inside library modules
- Use `pydantic_settings.BaseSettings` to load and validate config from env vars

## Testing
- Use `pytest` as the test framework
- Test pure logic (formatting, parsing), not external API calls
- Use Pydantic models to build test fixtures — no raw dicts in tests either
- Every test function must have a return type annotation of `-> None`
- Name test files `test_<module>.py` and test functions `test_<behavior>()`
