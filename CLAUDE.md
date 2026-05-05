# Remnant - CLAUDE.md

For Claude Code.

## Required startup

1. Look for `REMNANT.md` in the current project root.
2. If `REMNANT.md` exists, read it before touching project files.
3. If `REMNANT.md` is missing, create it from `REMNANT.template.md`.
4. If both files are missing, create `REMNANT.md` manually using the schema below.
5. Use `REMNANT.md` as a compact context map, not as full chat history.
6. Read only files needed for the current `## Next` task.

## Required shutdown

Before the final response, update `REMNANT.md` with a compact, non-sensitive handoff:

- `History`: roll the previous session's `Done` into one summary line, append to History (keep last 5, drop oldest)
- `Done`: this session's completed work only — fresh each session, not cumulative
- `Failed`: attempted work that failed and why
- `State`: current project state as a snapshot — replace fully, do not append
- `Next`: exact next task for a new context
- `Blockers`: unresolved decisions or dependencies

## Compression rule

Apply when: session exceeds 30 messages, context is approaching its limit, or the user requests it.

Steps:
1. Summarize decisions — what was decided and why, not the full discussion.
2. List changed files — paths only, no diffs or content.
3. Capture current state — what works, what is broken, what is in progress.
4. Write the exact next step — specific enough for a new agent to start without reading the conversation.
5. Record blockers — unresolved questions, decisions needed, or dependencies.

Never store secrets, credentials, tokens, private chat text, personal data, raw terminal output, or full conversation logs in `REMNANT.md`.
Never commit `REMNANT.md`; it is local-only and must stay in `.gitignore`.
Never use Remnant CLI commands; Remnant is Markdown-only.

## REMNANT.md schema

```markdown
# Remnant - <project-name>

## Session
- date: <ISO 8601>
- agent: <claude-code | codex | gemini-cli | antigravity | other>
- duration: <minutes>

## Done
- <completed work>

## Failed
- <failed attempt and reason>

## State
- <current state and important files>

## Next
- <exact next step>

## Blockers
- <open question or dependency>
```

## Project shape

```text
AGENTS.md            Codex and Google Antigravity instructions
CLAUDE.md            Claude Code instructions
GEMINI.md            Gemini CLI instructions
REMNANT.template.md  safe template to commit
REMNANT.md           local-only memory, ignored by Git
```
