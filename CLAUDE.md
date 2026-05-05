# Remnant

AI session context persistence — across agents, across projects, across time.

## What it does

At the end of each AI coding session, Remnant captures a structured snapshot of the project state (what was done, what failed, what's next) and persists it as a `REMNANT.md` file in the repo. At the start of the next session, it reinjects that context automatically so the agent resumes without re-explanation.

## Architecture

Two layers:

- **CLI** (`packages/cli`) — TypeScript/Bun. Runs inside the repo. Generates and injects `REMNANT.md`. Hooks into Claude Code and Codex session lifecycle.
- **Backend** (`packages/backend`) — Python/uv + FastAPI. Central store. Aggregates snapshots across all projects. Exposes a dashboard and REST API.

```
remnant/
├── packages/
│   ├── cli/               # Bun/TypeScript — per-repo agent
│   │   ├── src/
│   │   │   ├── capture.ts     # End-of-session snapshot generator
│   │   │   ├── inject.ts      # Start-of-session context injector
│   │   │   ├── schema.ts      # REMNANT.md schema + validator
│   │   │   └── sync.ts        # Push snapshot to backend
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── backend/           # Python/uv — central store
│       ├── app/
│       │   ├── main.py        # FastAPI entrypoint
│       │   ├── models.py      # Snapshot schema (Pydantic)
│       │   ├── store.py       # SQLite persistence
│       │   └── dashboard.py   # Aggregated project view
│       ├── pyproject.toml
│       └── .env.example
├── CLAUDE.md
├── AGENTS.md
├── .gitignore
└── README.md
```

## REMNANT.md schema

```markdown
# Remnant — <project-name>

## Session
- date: <ISO 8601>
- agent: <claude-code | codex | other>
- duration: <minutes>

## Done
- <what was completed this session>

## Failed
- <what was attempted and didn't work, with reason>

## State
- <current state of the codebase / key files touched>

## Next
- <exact next step to resume>

## Blockers
- <unresolved dependency, decision, or question>
```

## Commands

```bash
remnant init       # Init Remnant in current repo
remnant capture    # End of session — generate snapshot
remnant inject     # Start of session — inject context into agent prompt
remnant sync       # Push snapshot to central backend
remnant status     # View all projects dashboard (CLI)
```

## Key constraints

- `REMNANT.md` is committed to the repo — it is part of the codebase
- `REMNANT.md` is human-readable first, machine-parseable second
- The CLI never sends data to the backend without explicit `remnant sync`
- The backend stores snapshots as append-only — full history, no overwrite
- No auth required for local-only usage — backend is opt-in

## Stack

- CLI: TypeScript, Bun, Commander.js, Zod
- Backend: Python 3.12+, uv, FastAPI, SQLite (stdlib), Pydantic v2, Jinja2
- No ORM — raw SQL only
- Dashboard is server-rendered HTML — no frontend framework

## Security

- `.env` is gitignored — use `.env.example`
- Backend listens on `localhost` only by default
- No PII stored — snapshots contain only project state
- Run `bun audit` and `uv run pip-audit` before each release

## Development

```bash
# CLI
cd packages/cli && bun install && bun run dev

# Backend
cd packages/backend && uv sync && uv run uvicorn app.main:app --reload
```

## Out of scope (v1)

- Automatic capture without explicit `remnant capture`
- Cloud hosting of the backend
- Multi-user support
- IDE plugins
