# Project: Learning Sessions - Claude Code

## Tech Stack
- Language: Python 3.12+
- Dependency management: uv
- Environment variables: `.env` in root directory

## Commands
- Install deps: `uv sync`
- Run script: `uv run python <script.py>`
- Add package: `uv add <package>`
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`

## Code Style
- Use type hints for all function signatures
- Follow PEP 8 conventions
- Prefer f-strings over `.format()` or `%`
- Use `pathlib.Path` instead of `os.path`
- Use `httpx` for HTTP requests (async-first)

## Environment Variables
- Load from `.env` in root using `python-dotenv` or `pydantic-settings`
- Never hardcode secrets — always use env vars
- `.env` is gitignored; copy `.env.example` for setup

## Project Conventions
- Keep functions small and focused (< 30 lines)
- Write docstrings only for public APIs, not internal helpers
- Prefer returning values over raising exceptions for expected cases
- Use `logging` module, not `print()`, for debug output
