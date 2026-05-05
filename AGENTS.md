# Remnant — AGENTS.md

> Codex equivalent of CLAUDE.md. All architectural decisions are identical — read CLAUDE.md first for full context.

## Agent instructions

You are working on **Remnant**, a tool that persists AI session context across coding sessions. The goal: zero re-explanation when resuming a project with any AI agent.

## What to always do

- Read `REMNANT.md` at the start of every session before touching any file
- Write `REMNANT.md` at the end of every session using the schema below
- Never modify files outside the scope defined in `## Next` from the last snapshot
- If `REMNANT.md` does not exist, run `remnant init` first

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

## Monorepo structure

```
remnant/
├── packages/
│   ├── cli/           # TypeScript/Bun — remnant capture | inject | sync | status
│   └── backend/       # Python/uv — FastAPI + SQLite + Jinja2 dashboard
├── CLAUDE.md
├── AGENTS.md
└── .gitignore
```

## Allowed commands

```bash
# CLI
cd packages/cli
bun install
bun run build
bun run test

# Backend
cd packages/backend
uv sync
uv run pytest
uv run uvicorn app.main:app --reload --port 8421
```

## Constraints

- Do not install dependencies not listed in package.json or pyproject.toml without flagging it
- Do not write to .env — only .env.example
- Do not break the append-only constraint on the backend store
- Raw SQL only — no ORM
- Backend port default: 8421

## When blocked

Write the blocker in ## Blockers in REMNANT.md and stop. Do not guess.
