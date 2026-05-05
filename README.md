# Remnant

![Remnant logo](assets/remnant-logo.png)

No install. No server. No CLI. Just Markdown.

Remnant is a local memory protocol for AI coding agents. It uses one ignored project file, `REMNANT.md`, so a new Claude Code, Codex, Gemini CLI, or Google Antigravity session can resume without asking you to explain the project again.

## How It Works

Remnant keeps a compact handoff beside your code:

```text
REMNANT.md
|-- Session   date, agent, duration
|-- Done      completed work
|-- Failed    failed attempts and reason
|-- State     current project state and important files
|-- Next      exact next step
`-- Blockers  unresolved questions or dependencies
```

The file is human-readable first. Agents use it as a context map, not as full chat history.

## Setup

Add the instruction file for the agent you use:

```text
AGENTS.md   Codex and Google Antigravity
CLAUDE.md   Claude Code
GEMINI.md   Gemini CLI
```

Keep the safe template committed:

```text
REMNANT.template.md
```

Keep the real memory file local:

```text
REMNANT.md
```

Add this to `.gitignore`:

```gitignore
REMNANT.md
```

## Beginner Prompt

At the start of a session, tell the agent:

```text
Use Remnant. If REMNANT.md is missing, create it from REMNANT.template.md.
Read it before touching files. Before ending, update it with the final handoff.
```

That is enough. The agent instruction file tells the agent how to create, read, and update `REMNANT.md`.

## Agent Startup Rule

Every Remnant-compatible agent instruction file should say:

```text
1. Look for REMNANT.md in the current project root.
2. If REMNANT.md exists, read it before touching project files.
3. If REMNANT.md is missing, create it from REMNANT.template.md.
4. If both files are missing, create REMNANT.md manually using the schema.
5. Use REMNANT.md as a compact context map, not as full chat history.
```

## Agent Shutdown Rule

Before the final response, the agent updates `REMNANT.md`:

```text
Done      completed work only
Failed    failed attempts and reason
State     current project state and important files
Next      exact next task for a new context
Blockers  unresolved decisions or dependencies
```

Do not store secrets, credentials, tokens, private chat text, personal data, raw logs, or full chat history.

## Long Session Example

After a 50+ message session, do not paste the whole conversation into `REMNANT.md`. Compress it:

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

This preserves what matters for the next context without storing the full conversation.

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

`REMNANT.md` is local-only memory. It should stay ignored by Git.

Good content:

- decisions
- changed files
- current project state
- exact next action
- blockers

Bad content:

- secrets
- API keys
- credentials
- private chat logs
- personal data
- raw terminal dumps
- irrelevant history

## Current Package

```text
AGENTS.md            Codex and Google Antigravity instructions
CLAUDE.md            Claude Code instructions
GEMINI.md            Gemini CLI instructions
REMNANT.template.md  safe template to commit
REMNANT.md           local-only memory, ignored by Git
```
