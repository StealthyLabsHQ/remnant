# Remnant

![Remnant futuristic AI CLI logo](assets/remnant-logo.png)

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

## Compatible Agents

Remnant works by giving each agent the instruction file it actually reads, plus the shared `REMNANT.md` memory file.

```text
Claude Code          reads CLAUDE.md + REMNANT.md
Gemini CLI           reads GEMINI.md + REMNANT.md
Codex (OpenAI)       reads AGENTS.md + REMNANT.md
Google Antigravity   reads AGENTS.md + REMNANT.md
```

## CLI Usage

Install dependencies:

```bash
cd packages/cli
bun install
```

Initialize local memory at the repository root:

```bash
bun run src/index.ts init --file ../../REMNANT.md
```

Save context before switching agents:

```bash
bun run src/index.ts capture --file ../../REMNANT.md --next "Describe the exact next step"
```

Inject context into a new LLM session:

```bash
bun run src/index.ts inject --file ../../REMNANT.md
```

Check the current memory:

```bash
bun run src/index.ts status --file ../../REMNANT.md
```

Validate future sync readiness:

```bash
bun run src/index.ts sync --file ../../REMNANT.md
```

`sync` currently validates `REMNANT.md` and prints a placeholder. Backend sync is intentionally not implemented yet.

## Current Package

```text
packages/cli
├─ src/index.ts       Commander.js CLI
├─ src/schema.ts      Zod schema + REMNANT.md parser/renderer
└─ src/index.test.ts  Bun tests
```

## Test

```bash
cd packages/cli
bun install
bun run test
```
