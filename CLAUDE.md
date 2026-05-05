# Remnant — CLAUDE.md

For Claude Code.

## Required startup

1. Read `REMNANT.md` before touching files.
2. Use `REMNANT.md` as the context map, not as full chat history.
3. Read only files needed for the current `## Next` task.
4. If `REMNANT.md` is missing, run `remnant init` or copy `REMNANT.template.md`.

## Required shutdown

Before final response, update `REMNANT.md` with a compact, non-sensitive snapshot:

- `Done`: completed work only
- `Failed`: attempted work that failed and why
- `State`: current implementation state and key file paths
- `Next`: exact next task for a new context
- `Blockers`: unresolved decisions or dependencies

Do not store secrets, credentials, tokens, private chat text, personal data, or irrelevant logs in `REMNANT.md`.
Do not commit `REMNANT.md`; it is local-only memory and must stay ignored by Git.

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
packages/cli      Bun + TypeScript CLI
packages/backend  future Python/FastAPI backend
```

## Commands

```bash
cd packages/cli
bun install
bun run test
bun run build
```

## Constraints

- Smallest correct change.
- No new dependencies unless explicitly requested.
- Do not write `.env`; only `.env.example`.
- Do not commit secrets or local-only context.
- Backend store must remain append-only when implemented.
- Backend uses raw SQL only.
- Backend default port: 8421.
