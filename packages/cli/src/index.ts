#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";
import { Command, CommanderError } from "commander";
import { z } from "zod";
import {
  AgentSchema,
  RemnantSchema,
  createEmptyRemnant,
  parseRemnantMarkdown,
  renderRemnantMarkdown,
  type Agent,
  type Remnant,
} from "./schema";

type CliIO = {
  stdout: Pick<typeof process.stdout, "write">;
  stderr: Pick<typeof process.stderr, "write">;
};

type RunOptions = {
  cwd?: string;
  io?: CliIO;
};

const defaultFile = "REMNANT.md";

export async function run(argv: string[], options: RunOptions = {}): Promise<number> {
  const cwd = options.cwd ?? process.cwd();
  const io = options.io ?? { stdout: process.stdout, stderr: process.stderr };
  const program = buildProgram(cwd, io);

  try {
    await program.parseAsync(argv, { from: "user" });
    return 0;
  } catch (error) {
    if (error instanceof CommanderError) {
      return error.exitCode;
    }

    io.stderr.write(`${formatError(error)}\n`);
    return 1;
  }
}

function buildProgram(cwd: string, io: CliIO): Command {
  const program = new Command();

  program.name("remnant").description("Persist AI session context across coding sessions").exitOverride();

  program
    .command("init")
    .description("Init Remnant in current repo")
    .option("--file <path>", "REMNANT.md path", defaultFile)
    .option("--force", "overwrite existing REMNANT.md", false)
    .action((options: { file: string; force: boolean }) => {
      const file = resolve(cwd, options.file);
      if (existsSync(file) && !options.force) {
        throw new Error(`${options.file} already exists. Use --force to overwrite.`);
      }

      const remnant = createEmptyRemnant(projectNameFromPath(dirname(file)));
      writeFileSync(file, renderRemnantMarkdown(remnant), "utf8");
      io.stdout.write(`Initialized ${options.file}\n`);
    });

  program
    .command("capture")
    .description("Generate an end-of-session snapshot")
    .option("--file <path>", "REMNANT.md path", defaultFile)
    .option("--next <text>", "next step to resume from")
    .option("--agent <agent>", "agent name: claude-code, codex, or other", "codex")
    .option("--duration <minutes>", "session duration in minutes", parseDuration, 0)
    .action((options: { file: string; next?: string; agent: Agent; duration: number }) => {
      const agent = AgentSchema.parse(options.agent);
      const existing = readRemnant(cwd, options.file);
      const state = gitState(cwd);
      const next = options.next ? [options.next] : existing.next;

      if (next.length === 0) {
        throw new Error("capture requires --next when REMNANT.md has no existing Next section");
      }

      const remnant: Remnant = {
        ...existing,
        session: {
          date: new Date().toISOString(),
          agent,
          duration: options.duration,
        },
        state,
        next,
      };

      writeRemnant(cwd, options.file, remnant);
      io.stdout.write(`Captured ${options.file}\n`);
    });

  program
    .command("inject")
    .description("Print context for an agent prompt")
    .option("--file <path>", "REMNANT.md path", defaultFile)
    .action((options: { file: string }) => {
      const remnant = readRemnant(cwd, options.file);
      io.stdout.write(formatInject(remnant));
    });

  program
    .command("sync")
    .description("Validate snapshot before backend sync")
    .option("--file <path>", "REMNANT.md path", defaultFile)
    .action((options: { file: string }) => {
      readRemnant(cwd, options.file);
      io.stdout.write("backend sync not implemented\n");
    });

  program
    .command("status")
    .description("View current project snapshot status")
    .option("--file <path>", "REMNANT.md path", defaultFile)
    .action((options: { file: string }) => {
      const remnant = readRemnant(cwd, options.file);
      io.stdout.write(formatStatus(remnant));
    });

  return program;
}

function readRemnant(cwd: string, filePath: string): Remnant {
  const file = resolve(cwd, filePath);
  if (!existsSync(file)) {
    throw new Error(`${filePath} not found. Run 'remnant init' first.`);
  }

  return parseRemnantMarkdown(readFileSync(file, "utf8"));
}

function writeRemnant(cwd: string, filePath: string, remnant: Remnant): void {
  const file = resolve(cwd, filePath);
  writeFileSync(file, renderRemnantMarkdown(RemnantSchema.parse(remnant)), "utf8");
}

function gitState(cwd: string): string[] {
  const branch = runGit(cwd, ["branch", "--show-current"]);
  const status = runGit(cwd, ["status", "--short"]);
  const items: string[] = [];

  if (branch) {
    items.push(`branch: ${branch}`);
  }

  if (!status) {
    items.push("working tree clean");
    return items;
  }

  items.push("git status:");
  items.push(...status.split("\n").map((line) => line.trimEnd()));
  return items;
}

function runGit(cwd: string, args: string[]): string | null {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  if (result.status !== 0) {
    return null;
  }

  const output = result.stdout.trim();
  return output.length > 0 ? output : null;
}

function formatInject(remnant: Remnant): string {
  return [
    `Project: ${remnant.projectName}`,
    `Last session: ${remnant.session.date} (${remnant.session.agent}, ${remnant.session.duration}m)`,
    "",
    "Done:",
    formatPlainList(remnant.done),
    "",
    "Failed:",
    formatPlainList(remnant.failed),
    "",
    "State:",
    formatPlainList(remnant.state),
    "",
    "Next:",
    formatPlainList(remnant.next),
    "",
    "Blockers:",
    formatPlainList(remnant.blockers),
    "",
  ].join("\n");
}

function formatStatus(remnant: Remnant): string {
  return [
    `Project: ${remnant.projectName}`,
    `Session: ${remnant.session.date} (${remnant.session.agent}, ${remnant.session.duration}m)`,
    `Next: ${remnant.next[0] ?? "none"}`,
    `Blockers: ${remnant.blockers.length === 0 ? "none" : remnant.blockers.join("; ")}`,
    "",
  ].join("\n");
}

function formatPlainList(items: string[]): string {
  if (items.length === 0) {
    return "- none";
  }

  return items.map((item) => `- ${item}`).join("\n");
}

function projectNameFromPath(path: string): string {
  return basename(path) || "project";
}

function parseDuration(value: string): number {
  const duration = Number.parseInt(value, 10);
  if (!Number.isInteger(duration) || duration < 0) {
    throw new Error("--duration must be a non-negative integer");
  }

  return duration;
}

function formatError(error: unknown): string {
  if (error instanceof z.ZodError) {
    return `Invalid REMNANT.md: ${error.errors.map((item) => item.message).join("; ")}`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}

if (import.meta.main) {
  const exitCode = await run(process.argv.slice(2));
  process.exit(exitCode);
}
