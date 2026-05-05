# Remnant — AGENTS.md

For Codex and Google Antigravity.

## Required startup

1. Read `REMNANT.md` before touching files.
2. Use `REMNANT.md` as the context map, not as full chat history.
3. Read only files needed for the current `## Next` task.
4. If `REMNANT.md` is missing, run `remnant init` or copy `REMNANT.template.md`.
5. If the user is switching between many projects, use `remnant status --all`, `remnant status --search <query>`, or `remnant search <query>` to find indexed local project memories.
6. If the user says "use remnant", search the local Remnant index first, then read the matching project `REMNANT.md`.

## Required shutdown

Before final response, update `REMNANT.md` with a compact, non-sensitive snapshot:

- `Done`: completed work only
- `Failed`: attempted work that failed and why
- `State`: current implementation state and key file paths
- `Next`: exact next task for a new context
- `Blockers`: unresolved decisions or dependencies

Do not store secrets, credentials, tokens, private chat text, personal data, or irrelevant logs in `REMNANT.md`.
Do not commit `REMNANT.md`; it is local-only memory and must stay ignored by Git.
The global index at `~/.remnant/projects.json` is local-only and should contain only project paths plus short `Next` summaries.

## REMNANT.md schema

```markdown
# Remnant — <project-name>

## Session
- date: <ISO 8601>
- agent: <claude-code | codex | gemini-cli | antigravity | other>
- duration: <minutes>

## Done
- <completed work>

## Failed
- <failed attempt and reason>

## State
- <current state and key files>

## Next
- <exact next step>

## Blockers
- <open question or dependency>
```

## Project shape

```text
packages/cli      Python/uv + Typer CLI
packages/backend  future Python/FastAPI backend
```

## Commands

```bash
cd packages/cli
uv sync
uv run pytest
```

## Constraints

- Smallest correct change.
- No new dependencies unless explicitly requested.
- Do not write `.env`; only `.env.example`.
- Do not commit secrets or local-only context.
- Backend store must remain append-only when implemented.
- Backend uses raw SQL only.
- Backend default port: 8421.
