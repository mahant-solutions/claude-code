# Learning Claude Code

A structured, hands-on journey through [Claude Code](https://claude.ai/claude-code) — Anthropic's AI-powered coding assistant for the terminal.

## What is Claude Code?

Claude Code is a command-line tool that brings Claude directly into your development workflow. It can:

- Read and edit files in your codebase
- Run terminal commands
- Search and navigate large projects
- Help debug, refactor, and write code
- Create and manage git commits and pull requests

## Tech Stack

Examples in this repo use:

- **Python 3.12+** with **uv** for dependency management
- **python-dotenv** / **pydantic-settings** to load `.env` from the repo root
- **ruff** for linting and formatting, **pytest** for tests

```bash
uv sync                        # install dependencies
uv run python <script.py>      # run a script
uv run pytest                  # run tests
```

## Getting Started with Claude Code

### Installation

```bash
npm install -g @anthropic-ai/claude-code
```

### Running Claude Code

```bash
claude
```

### Useful Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation context |
| `/compact` | Compress conversation history |
| `/cost` | Show token usage and cost |
| `/exit` | Exit Claude Code |

## Topics Covered

| # | Topic | Description |
|---|-------|-------------|
| 1 | **Basics** | Navigation, file editing, and shell commands |
| 2 | **CLAUDE.md** | Project instructions and conventions for Claude |
| 3 | **Skills** | Custom slash commands and reusable prompts |
| 4 | **MCPs** | Model Context Protocol server integrations |
| 5 | **Sub-agents** | Spawning and coordinating specialized agents |
| 6 | **Modes** | Plan mode, auto-accept, and permission modes |
| 7 | **Version Management** | Git workflow automation |
| 8 | **Commands** | Advanced CLI usage and hooks |

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Anthropic Website](https://www.anthropic.com)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)

---

*Happy coding with Claude!*
