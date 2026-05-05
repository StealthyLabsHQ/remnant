# Remnant

![Remnant logo](assets/remnant-logo.png)

No install. No server. No CLI. Just Markdown.

Remnant is a session memory protocol for AI coding agents. One ignored file, `REMNANT.md`, lets Claude Code, Codex, Gemini CLI, or Antigravity resume a session without asking you to re-explain the project.

## How It Works

The agent reads `REMNANT.md` at startup and writes a compact handoff before ending:

```text
REMNANT.md
|-- Session   date, agent, duration
|-- Done      completed work
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
Done      completed work only
Failed    failed attempts and reason
State     current project state and important files
Next      exact next task for a new context
Blockers  unresolved decisions or dependencies
```

## Example

A compressed handoff after a long session:

```markdown
# Remnant - remnant

## Session
- date: 2026-05-05T12:00:00Z
- agent: codex
- duration: 90

## Done
- Repositioned Remnant as a Markdown-only protocol.
- Removed the CLI and install scripts.
- Updated agent instruction files to create and maintain REMNANT.md directly.

## Failed
- CLI-based install flow confused users because it looked successful without obvious files.

## State
- Public docs now lead with zero-install Markdown usage.
- `REMNANT.md` is local-only and ignored by Git.
- `REMNANT.template.md` is the committed safe starting point.

## Next
- Review the README for beginner clarity and publish the Markdown-only direction.

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
