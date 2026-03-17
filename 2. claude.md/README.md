# 2. CLAUDE.md Demo

This folder demonstrates how `CLAUDE.md` guides Claude's code generation.

## What is CLAUDE.md?

A file Claude reads at the start of every conversation. It tells Claude:
- What tech stack to use
- What commands to run
- What rules to follow when writing code

## How this demo shows it

The [CLAUDE.md](CLAUDE.md) in this folder defines rules + testing conventions. Every file follows them:

| Rule in CLAUDE.md | Where you can see it |
|---|---|
| **Rules** | |
| API keys from env vars, never hardcoded | `config.py` — `BaseSettings` loads from `.env` |
| Pydantic models for API responses | `models.py` — structured models, no raw dicts |
| `pathlib.Path` for file ops | No `os.path` usage anywhere |
| `logging` instead of `print()` | `weather.py` — uses `logger.error()` for errors |
| Functions under 20 lines | Every function is small and focused |
| Type hints on all signatures | Every function has full type annotations |
| Return `None` on errors, don't raise | `fetch_weather()` returns `None` on failure |
| **Design Best Practices** | |
| Separate I/O from pure logic | `fetch_weather()` does I/O, `format_weather()` is pure |
| Constants for magic values | `CURRENT_WEATHER_ENDPOINT` — no inline strings |
| `httpx.Client` with timeout | `weather.py` — uses client context manager with timeout |
| Logging config at entry point | `main.py` — `logging.basicConfig()`, not in library modules |
| `pydantic_settings.BaseSettings` for config | `config.py` — validates env vars with types |
| **Testing** | |
| Test pure logic, not external APIs | `test_weather.py` — tests `format_weather()`, not the API call |
| Pydantic models as test fixtures | `test_weather.py` — builds `WeatherResponse` objects, no raw dicts |
| Test functions annotated `-> None` | Every test has `-> None` return type |
| Naming: `test_<module>.py` / `test_<behavior>()` | File is `test_weather.py`, function is `test_format_weather()` |

## Try it

```bash
cd "2. claude.md"
cp .env.example .env          # add your weatherapi.com key
uv sync
uv run pytest                 # run tests
uv run python main.py London  # fetch weather
```

## The point

Without `CLAUDE.md`, Claude might use `requests`, skip type hints, hardcode keys, or use raw dicts. The `CLAUDE.md` file ensures **consistent, project-specific code** every time.
