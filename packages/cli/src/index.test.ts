import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { run } from "./index";
import { createEmptyRemnant, parseRemnantMarkdown, renderRemnantMarkdown } from "./schema";

let cwd = "";

beforeEach(() => {
  cwd = mkdtempSync(join(tmpdir(), "remnant-cli-"));
});

afterEach(() => {
  rmSync(cwd, { recursive: true, force: true });
});

describe("REMNANT.md schema", () => {
  test("parses rendered markdown", () => {
    const source = createEmptyRemnant("example");
    const parsed = parseRemnantMarkdown(renderRemnantMarkdown(source));

    expect(parsed.projectName).toBe("example");
    expect(parsed.session.agent).toBe("codex");
  });
});

describe("commands", () => {
  test("init creates valid markdown", async () => {
    const io = captureIO();
    const code = await run(["init"], { cwd, io });

    expect(code).toBe(0);
    const parsed = parseRemnantMarkdown(readFileSync(join(cwd, "REMNANT.md"), "utf8"));
    expect(parsed.projectName).toMatch(/^remnant-cli-/);
  });

  test("capture includes git-derived state", async () => {
    spawnSync("git", ["config", "user.email", "test@remnant.local"], { cwd });
    spawnSync("git", ["config", "user.name", "Remnant Test"], { cwd });
    spawnSync("git", ["init"], { cwd });
    spawnSync("git", ["checkout", "-b", "feature/test"], { cwd });
    writeFileSync(join(cwd, "tracked.txt"), "content", "utf8");
    spawnSync("git", ["add", "tracked.txt"], { cwd });

    await run(["init"], { cwd, io: captureIO() });
    const io = captureIO();
    const code = await run(["capture", "--next", "continue CLI work"], { cwd, io });
    const parsed = parseRemnantMarkdown(readFileSync(join(cwd, "REMNANT.md"), "utf8"));

    expect(code).toBe(0);
    expect(parsed.state).toContain("branch: feature/test");
    expect(parsed.state).toContain("git status:");
    // Staged file detected.
    expect(parsed.state.some((item) => item.includes("tracked.txt"))).toBe(true);
  });

  test("init --force overwrites existing REMNANT.md", async () => {
    await run(["init"], { cwd, io: captureIO() });
    const code = await run(["init", "--force"], { cwd, io: captureIO() });

    expect(code).toBe(0);
  });

  test("capture without --next on empty REMNANT.md fails clearly", async () => {
    await run(["init"], { cwd, io: captureIO() });
    const io = captureIO();
    const code = await run(["capture"], { cwd, io });

    expect(code).toBe(1);
    expect(io.err()).toContain("--next");
  });

  test("inject fails clearly when REMNANT.md is missing", async () => {
    const io = captureIO();
    const code = await run(["inject"], { cwd, io });

    expect(code).toBe(1);
    expect(io.err()).toContain("REMNANT.md not found");
  });

  test("sync validates and prints placeholder", async () => {
    await run(["init"], { cwd, io: captureIO() });
    const io = captureIO();
    const code = await run(["sync"], { cwd, io });

    expect(code).toBe(0);
    expect(io.out()).toBe("backend sync not implemented\n");
  });

  test("status fails clearly when REMNANT.md is invalid", async () => {
    writeFileSync(join(cwd, "REMNANT.md"), "invalid", "utf8");
    const io = captureIO();
    const code = await run(["status"], { cwd, io });

    expect(code).toBe(1);
    expect(io.err()).toContain("Invalid REMNANT.md");
  });
});

function captureIO() {
  let stdout = "";
  let stderr = "";

  return {
    stdout: {
      write(chunk: string) {
        stdout += chunk;
        return true;
      },
    },
    stderr: {
      write(chunk: string) {
        stderr += chunk;
        return true;
      },
    },
    out: () => stdout,
    err: () => stderr,
  };
}
