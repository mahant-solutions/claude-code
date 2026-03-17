# Claude Code

### North Star
> **Software Building Lifecycle → we want this faster.**

#### Current Software Building Lifecycle
1. Idea
2. Design
3. Implementation
4. Testing
5. Deployment
6. Monitoring
7. Iteration

### How It Works
Claude Code is built on an **LLM + Agent** foundation

- Coding Agent(Claude code with bash tool)

---

### Key Building Blocks

**CLAUDE.md** — the project context file that instructs the agent. Supports **nesting**, so you can have global + project-level + subdirectory-level configs.

**Skills** — reusable capability modules the agent can draw on.

**MCPs (Model Context Protocol servers)** — extend the agent's reach into external systems. Key categories:
- `docs` — documentation servers
- `infra` — infrastructure/tooling servers

**Subagents** — specialized agents that handle delegated subtasks within a larger workflow.

Misc Integrations:
- **GitHub CLI** — for repo management, branching, PRs.

---

### Workflow Patterns

**Plan Mode vs Execution Mode** — separating the *thinking* step (choosing a model/approach) from the *doing* step.
- Plan Mode: Slower/Better models
- Execution Mode: Faster/Cheaper models

**Version management** — structured feature development with commits per feature iteration (F1.1 → F1.2) and test-driven development as the discipline holding it together.

**Commands** — slash commands or custom commands that trigger specific agent behaviors.

---

### Productivity

#### Whispr Flow
Voice to text service that integrates with almost any input interface.

#### Prompt Repository
A centralized store of reusable prompts — feeding into the broader **Whisper Flow** pipeline.
