# Remnant

![Remnant logo](assets/remnant-logo.png)

No install. No server. No CLI. Just Markdown.

Remnant is a session memory protocol for AI coding agents. One ignored file, `REMNANT.md`, lets Claude Code, Codex, Gemini CLI, or Antigravity resume a session without asking you to re-explain the project.

## How It Works

The agent reads `REMNANT.md` at startup and writes a compact handoff before ending:

```text
REMNANT.md
|-- Session   date, agent, duration
|-- History   one-line summaries of previous sessions (max 5)
|-- Done      completed work this session
|-- Failed    failed attempts and reason
|-- State     current project state and important files
|-- Next      exact next step
`-- Blockers  unresolved questions or dependencies
```

The file is human-readable. Agents use it as a context map, not as full chat history.

## Setup

**1. Copy the instruction file for your agent into your project root:**

| Agent | File |
|-------|------|
| Claude Code | `CLAUDE.md` |
| Codex / Antigravity | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |

**2. Copy `REMNANT.template.md` into your project root.**

**3. Add `REMNANT.md` to `.gitignore`:**

```gitignore
REMNANT.md
```

`REMNANT.md` is created automatically the first time the agent runs.

## Starting a Session

Tell the agent once at the start of a new project:

```text
Use Remnant. If REMNANT.md is missing, create it from REMNANT.template.md.
Read it before touching files. Before ending, update it with the final handoff.
```

After that, the instruction files handle startup and shutdown automatically.

## When Context Is Getting Full

If a session runs long or the context window is filling up, ask the agent to compress:

```text
Compress the session into REMNANT.md: decisions, changed files, current state, exact next step, blockers.
```

The agent writes a summary, not a transcript. It captures only what a new agent needs to continue.

## Agent Rules

### Startup

1. Look for `REMNANT.md` in the project root.
2. If it exists, read it before touching any files.
3. If it is missing, create it from `REMNANT.template.md`.
4. If both are missing, create `REMNANT.md` using the schema below.
5. Read only files needed for the current `## Next` task.

### Shutdown

Before the final response, update `REMNANT.md`:

```text
History   roll previous Done into one line (keep last 5, drop oldest)
Done      this session's completed work only — fresh each session
Failed    failed attempts and reason
State     current project state as a snapshot — replace, do not append
Next      exact next task for a new context
Blockers  unresolved decisions or dependencies
```

## Example

A compressed handoff after multiple sessions:

```markdown
# Remnant - remnant

## Session
- date: 2026-05-05T14:00:00Z
- agent: claude-code
- duration: 30

## History
- 2026-05-04 (codex, 90m): repositioned as Markdown-only protocol, removed CLI and install scripts

## Done
- Improved compression rule in agent files.
- Restructured README for beginner clarity.

## Failed
- None.

## State
- All agent files consistent.
- README restructured, zero-install preserved.

## Next
- Review and publish.

## Blockers
- None.
```

## Schema

```markdown
# Remnant - <project-name>

## Session
- date: <ISO 8601>
- agent: <claude-code | codex | gemini-cli | antigravity | other>
- duration: <minutes>

## History
- <one-line summary per previous session — oldest first, max 5 — or "None">

## Done
- <completed work — this session only>

## Failed
- <failed attempt and reason>

## State
- <current state as a snapshot — replace each session>

## Next
- <exact next step>

## Blockers
- <open question or dependency>
```

## Security

`REMNANT.md` is local-only. Keep it in `.gitignore`.

Write:
- decisions and rationale
- changed file paths
- current project state
- exact next action
- blockers

Never write:
- secrets, API keys, credentials
- private chat logs or personal data
- raw terminal output or build logs
- irrelevant history

## Files

```text
AGENTS.md            Codex and Google Antigravity instructions
CLAUDE.md            Claude Code instructions
GEMINI.md            Gemini CLI instructions
REMNANT.template.md  safe template to commit
REMNANT.md           local-only memory, ignored by Git
```
