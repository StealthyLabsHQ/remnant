# Remnant — remnant

## Session
- date: 2026-05-05T12:21:05.2540900+02:00
- agent: codex
- duration: 65

## Done
- Built packages/cli as a Bun + TypeScript CLI using Commander.js and Zod.
- Added commands: init, capture, inject, sync, status.
- Added REMNANT.md Markdown parser/renderer and Zod validation.
- Added Bun tests for schema roundtrip, init, capture, inject, sync, and status.
- Fixed CLI tests for git config, staged file capture, init --force, and capture without --next.
- Verified packages/cli with bun run test: 8 pass, 0 fail.
- Added README.md with CLI-style Remnant branding, usage, local storage behavior, and compatibility notes for Claude Code, Codex, Gemini CLI, and Google Antigravity.
- Initialized local git repository, committed the project, created private GitHub repo https://github.com/StealthyLabsHQ/remnant, and pushed main.
- Added GEMINI.md so Gemini CLI has a native instruction file.
- Corrected README agent compatibility: Claude Code reads CLAUDE.md, Gemini CLI reads GEMINI.md, Codex and Google Antigravity read AGENTS.md.

## Failed
- Initial repo root git status failed before git init because the directory was not yet a git repository.

## State
- Key files created or changed under packages/cli: package.json, tsconfig.json, src/index.ts, src/schema.ts, src/index.test.ts.
- REMNANT.md has now been initialized at the repo root.
- sync command is intentionally a placeholder: it validates REMNANT.md and prints "backend sync not implemented".
- node_modules was installed only with bun install --no-save for validation, then removed.
- README.md exists at the repo root and explains how Remnant stores context locally in REMNANT.md.
- Git remote origin tracks https://github.com/StealthyLabsHQ/remnant.git.
- Agent instruction files now exist for Claude Code, Gemini CLI, Codex, and Google Antigravity.

## Next
- Decide whether to add backend integration for remnant sync or keep iterating on the CLI package.

## Blockers
- No backend package exists yet, so sync cannot send snapshots anywhere.
