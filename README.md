# Remnant

![Remnant CLI-style logo](assets/remnant-logo.png)

Remnant is a local memory file for AI coding agents. It writes the current project state to an ignored local `REMNANT.md` so a new Claude Code, Codex, Gemini CLI, or Google Antigravity session can resume without asking you to explain the project again.

## How It Works

Remnant stores context in plain Markdown beside your code:

```text
REMNANT.md
├─ Session   date, agent, duration
├─ Done      what was completed
├─ Failed    what did not work and why
├─ State     current codebase state
├─ Next      exact next step
└─ Blockers  unresolved questions or dependencies
```

The file is human-readable first and machine-parseable second. `REMNANT.md` is ignored by Git because it can contain local project context. Commit `REMNANT.template.md`, not `REMNANT.md`.

## Local Storage

Remnant remembers by writing `REMNANT.md` in the repository root. That makes the memory:

- local to your machine and project
- visible to any CLI agent that can read files
- safe from accidental commits
- editable by humans
- independent from any single LLM vendor

For many projects, the optional CLI also keeps a decentralized local index:

```text
~/.remnant/projects.json
```

That index stores project paths and last `## Next` values so an agent can find recent project memory without using Codex, Claude, Gemini, or any cloud memory.

This is the Remnant version of Context7-style lookup, but local-only:

```text
Context7: fetch external docs into an LLM prompt
Remnant:  find local project memory and read REMNANT.md
```

No localhost server, no MCP server, no API key, no cloud memory.

## Compatible Agents

Remnant works by giving each agent the instruction file it actually reads, plus the shared `REMNANT.md` memory file.

```text
Claude Code          reads CLAUDE.md + REMNANT.md
Gemini CLI           reads GEMINI.md + REMNANT.md
Codex (OpenAI)       reads AGENTS.md + REMNANT.md
Google Antigravity   reads AGENTS.md + REMNANT.md
```

## Beginner Setup

You do not need to install a CLI to use Remnant.

Add these files to your project:

```text
CLAUDE.md             for Claude Code
AGENTS.md             for Codex and Google Antigravity
GEMINI.md             for Gemini CLI
REMNANT.template.md   safe template to commit
```

Then create your private local memory file:

```text
copy REMNANT.template.md to REMNANT.md
```

Keep `REMNANT.md` ignored by Git:

```gitignore
REMNANT.md
```

That is enough. The agent instruction file tells the agent to read and update `REMNANT.md`.

## Easy Command Install

If you want to type `remnant install claude` in Command Prompt, install the command once.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/StealthyLabsHQ/remnant/main/install.ps1 | iex"
```

macOS Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/StealthyLabsHQ/remnant/main/install.sh | sh
```

This downloads Remnant from GitHub into:

```text
%USERPROFILE%\.remnant\remnant
~/.remnant/remnant
```

Then close and reopen Command Prompt or Terminal.

Test:

```bash
remnant --help
```

Start the interactive Remnant CLI:

```cmd
remnant
```

Then type `/` to show commands:

```text
/
/install claude
/install codex
/install gemini
/install antigravity
/install all
/init
/capture continue the current task
/sync
/status
/search backend
/exit
```

Now these work from any project:

```cmd
remnant install claude
remnant install codex
remnant install gemini
remnant install antigravity
remnant install all
```

If you run install from your home folder, Remnant installs global agent instructions here:

```text
%USERPROFILE%\.claude\CLAUDE.md
%USERPROFILE%\.codex\AGENTS.md
%USERPROFILE%\.gemini\GEMINI.md
~/.claude/CLAUDE.md
~/.codex/AGENTS.md
~/.gemini/GEMINI.md
```

Existing `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` content is preserved. Remnant only appends a `## Remnant Integration` section.

If you run install inside a project folder, Remnant adds project-local instructions:

```text
.claude\CLAUDE.md
AGENTS.md
GEMINI.md
```

Project-local instruction files are append-only too. Remnant does not delete or rewrite your existing rules.

If `remnant` is not recognized, the PATH update has not loaded yet. Open a new Command Prompt or Terminal and try again.

## No Paste Setup For Claude Code

Remnant can add persistent project instructions so you do not need to paste "read REMNANT.md" every time.

For Claude Code, Remnant writes `.claude` integration files and appends a Remnant block to root `CLAUDE.md`:

```bash
remnant install claude
```

This creates:

```text
.claude/CLAUDE.md
.claude/settings.json
.claude/hooks/remnant_session_start.py
```

Claude Code loads `.claude/CLAUDE.md` at startup. The `SessionStart` hook also injects local `REMNANT.md` into Claude's context automatically, so you do not need to paste "read REMNANT.md" every time.

Use `--force` to overwrite existing Remnant-managed Claude files:

```bash
remnant install claude --force
```

`--force` only overwrites Remnant-managed `.claude/settings.json` and `.claude/hooks/remnant_session_start.py`. It still appends to instruction Markdown files instead of replacing them.

For Codex:

```bash
remnant install codex
```

This appends a Remnant block to root `AGENTS.md`.

For Google Antigravity:

```bash
remnant install antigravity
```

This appends a Remnant block to root `AGENTS.md`.

For Gemini CLI:

```bash
remnant install gemini
```

This appends a Remnant block to root `GEMINI.md`.

Install every supported local integration:

```bash
remnant install all
```

## Daily Use

At the start of a new context, tell the agent:

```text
Read your instruction file and REMNANT.md first, then continue from ## Next.
```

Before ending or switching context, tell the agent:

```text
Update REMNANT.md with Done, Failed, State, Next, and Blockers.
```

## Optional CLI

The CLI is optional. Use it only if you want commands instead of manual editing.

Developer install:

```bash
cd packages/cli
uv sync
```

Initialize local memory at the repository root:

```bash
uv run remnant init --file ../../REMNANT.md
```

Do not run `remnant init` from your home folder. Run it inside a project folder so `REMNANT.md` belongs to that project.

Save context before switching agents:

```bash
uv run remnant capture --file ../../REMNANT.md --next "Describe the exact next step"
```

Inject context into a new LLM session:

```bash
uv run remnant inject --file ../../REMNANT.md
```

Check the current memory:

```bash
uv run remnant status --file ../../REMNANT.md
```

List all indexed projects:

```bash
uv run remnant status --all
```

Search indexed project memories:

```bash
uv run remnant status --search "checkout bug"
```

Or use the shorter search command:

```bash
uv run remnant search "checkout bug"
```

Validate future sync readiness:

```bash
uv run remnant sync --file ../../REMNANT.md
```

`sync` currently validates `REMNANT.md` and prints a placeholder. Backend sync is intentionally not implemented yet.

## Current Package

```text
packages/cli
├─ src/remnant_cli/main.py    Typer CLI
├─ src/remnant_cli/schema.py  REMNANT.md parser/renderer
└─ tests/test_cli.py          pytest coverage
```

## Test

```bash
cd packages/cli
uv sync
uv run pytest
```
