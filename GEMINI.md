# Remnant — GEMINI.md

You are working on Remnant, a tool that persists AI session context across coding sessions.

## Required startup

- Read `REMNANT.md` before touching files.
- If `REMNANT.md` does not exist, run `remnant init` first.
- Keep changes scoped to the current `## Next` section in `REMNANT.md`.

## Required shutdown

Update `REMNANT.md` with:

- what was completed
- what failed and why
- current project state
- exact next step
- blockers

## Project shape

```text
packages/cli      Bun + TypeScript CLI
packages/backend  future Python/FastAPI backend
```

## CLI commands

```bash
cd packages/cli
bun install
bun run test
bun run build
```

## Constraints

- No new dependencies unless explicitly requested.
- Do not write `.env`; only `.env.example`.
- Do not break the backend append-only store when it exists.
- Raw SQL only for backend work.
- Backend default port: 8421.
