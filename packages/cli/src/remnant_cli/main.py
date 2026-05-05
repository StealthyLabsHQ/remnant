from __future__ import annotations

import subprocess
import sys
import json
import shlex
from dataclasses import replace
from pathlib import Path
from typing import Annotated, Literal

import typer

from remnant_cli.schema import (
    Agent,
    create_empty_remnant,
    parse_remnant_markdown,
    render_remnant_markdown,
    validate_remnant,
)

app = typer.Typer(help="Persist AI session context across coding sessions.", invoke_without_command=True)
DEFAULT_FILE = "REMNANT.md"
SHELL_COMMANDS = [
    ("/install <agent>", "install claude, codex, gemini, antigravity, or all"),
    ("/init", "create REMNANT.md in the current project"),
    ("/capture <next>", "save the next step and current git state"),
    ("/inject", "print compact context for an agent prompt"),
    ("/sync", "validate local memory; backend sync is not implemented"),
    ("/status", "show this project memory status"),
    ("/status --all", "list indexed project memories"),
    ("/search <query>", "search indexed project memories"),
    ("/exit", "leave the Remnant shell"),
]
SHELL_LOGO = r"""
REMNANT.
######  ####### #     # #     #  ###  #     # #######
#     # #       ##   ## ##    # #   # ##    #    #
######  #####   # # # # # #   # ##### # #   #    #
#   #   #       #  #  # #  #  # #   # #  #  #    #
#    #  ####### #     # #   ### #   # #   ###    #
"""


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Open Remnant shell when no command is provided."""
    if ctx.invoked_subcommand is None:
        _run_shell()


@app.command()
def init(
    file: Annotated[str, typer.Option("--file", help="REMNANT.md path")] = DEFAULT_FILE,
    force: Annotated[bool, typer.Option("--force", help="overwrite existing REMNANT.md")] = False,
) -> None:
    """Init Remnant in current repo."""
    if file == DEFAULT_FILE and Path.cwd().resolve() == Path.home().resolve():
        _fail("Refusing to create REMNANT.md in the home folder. Run inside a project or pass --file.")

    path = Path(file).resolve()
    if path.exists() and not force:
        _fail(f"{file} already exists. Use --force to overwrite.")

    remnant = create_empty_remnant(path.parent.name)
    path.write_text(render_remnant_markdown(remnant), encoding="utf-8")
    _update_project_index(path, remnant)
    typer.echo(f"Initialized {file}")


@app.command()
def capture(
    file: Annotated[str, typer.Option("--file", help="REMNANT.md path")] = DEFAULT_FILE,
    next: Annotated[str | None, typer.Option("--next", help="next step to resume from")] = None,
    agent: Annotated[Agent, typer.Option("--agent", help="agent name")] = "codex",
    duration: Annotated[int, typer.Option("--duration", help="session duration in minutes")] = 0,
) -> None:
    """Generate an end-of-session snapshot."""
    if duration < 0:
        _fail("--duration must be a non-negative integer")

    existing = _read_remnant(file)
    next_items = [next] if next else existing.next
    if not next_items:
        _fail("capture requires --next when REMNANT.md has no existing Next section")

    remnant = replace(
        existing,
        session=replace(existing.session, date=_now_iso(), agent=agent, duration=duration),
        state=_git_state(Path.cwd()),
        next=next_items,
    )
    _write_remnant(file, remnant)
    _update_project_index(Path(file).resolve(), remnant)
    typer.echo(f"Captured {file}")


@app.command()
def inject(file: Annotated[str, typer.Option("--file", help="REMNANT.md path")] = DEFAULT_FILE) -> None:
    """Print context for an agent prompt."""
    remnant = _read_remnant(file)
    typer.echo(_format_inject(remnant), nl=False)


@app.command()
def sync(file: Annotated[str, typer.Option("--file", help="REMNANT.md path")] = DEFAULT_FILE) -> None:
    """Validate snapshot before backend sync."""
    _read_remnant(file)
    typer.echo("backend sync not implemented")


@app.command()
def status(
    file: Annotated[str, typer.Option("--file", help="REMNANT.md path")] = DEFAULT_FILE,
    all: Annotated[bool, typer.Option("--all", help="show all indexed projects")] = False,
    search: Annotated[str | None, typer.Option("--search", help="search indexed projects")] = None,
) -> None:
    """View current project snapshot status."""
    if all or search:
        typer.echo(_format_project_index(search))
        return

    remnant = _read_remnant(file)
    blockers = "none" if not remnant.blockers else "; ".join(remnant.blockers)
    next_item = remnant.next[0] if remnant.next else "none"
    typer.echo(
        "\n".join(
            [
                f"Project: {remnant.project_name}",
                f"Session: {remnant.session.date} ({remnant.session.agent}, {remnant.session.duration}m)",
                f"Next: {next_item}",
                f"Blockers: {blockers}",
                "",
            ]
        )
    )


@app.command()
def search(query: str) -> None:
    """Search local Remnant project memories."""
    typer.echo(_format_project_index(query))


@app.command()
def install(
    agent: Annotated[
        Literal["claude", "codex", "gemini", "antigravity", "all"],
        typer.Argument(help="agent integration to install"),
    ],
    force: Annotated[bool, typer.Option("--force", help="overwrite existing Remnant-managed files")] = False,
    scope: Annotated[
        Literal["auto", "project", "global"],
        typer.Option("--scope", help="install scope: auto, project, or global"),
    ] = "auto",
) -> None:
    """Install agent integration files."""
    install_scope = _resolve_install_scope(scope)
    installed_paths: list[str] = []
    if agent in ("claude", "all"):
        installed_paths.extend(_install_claude(force, install_scope))
    if agent in ("codex", "all"):
        installed_paths.append(_append_agent_block(_agent_instruction_path("codex", install_scope), "Codex"))
    if agent in ("antigravity", "all"):
        installed_paths.append(
            _append_agent_block(_agent_instruction_path("codex", install_scope), "Google Antigravity")
        )
    if agent in ("gemini", "all"):
        installed_paths.append(_append_agent_block(_agent_instruction_path("gemini", install_scope), "Gemini CLI"))
    typer.echo(f"Installed {agent} Remnant integration ({install_scope})")
    for installed_path in installed_paths:
        typer.echo(f"- {installed_path}")


def _read_remnant(file: str):
    path = Path(file).resolve()
    if not path.exists():
        _fail(f"{file} not found. Run 'remnant init' first.")
    try:
        return parse_remnant_markdown(path.read_text(encoding="utf-8"))
    except ValueError as error:
        _fail(str(error))


def _write_remnant(file: str, remnant) -> None:
    validate_remnant(remnant)
    Path(file).resolve().write_text(render_remnant_markdown(remnant), encoding="utf-8")


def _git_state(cwd: Path) -> list[str]:
    branch = _run_git(cwd, ["branch", "--show-current"])
    status = _run_git(cwd, ["status", "--short"])
    items: list[str] = []

    if branch:
        items.append(f"branch: {branch}")

    if not status:
        items.append("working tree clean")
        return items

    items.append("git status:")
    items.extend(status.split("\n"))
    return items


def _run_git(cwd: Path, args: list[str]) -> str | None:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def _resolve_install_scope(scope: Literal["auto", "project", "global"]) -> Literal["project", "global"]:
    if scope != "auto":
        return scope
    return "global" if Path.cwd().resolve() == Path.home().resolve() else "project"


def _agent_instruction_path(agent: Literal["claude", "codex", "gemini"], scope: Literal["project", "global"]) -> Path:
    if scope == "global":
        if agent == "claude":
            return Path.home() / ".claude" / "CLAUDE.md"
        if agent == "codex":
            return Path.home() / ".codex" / "AGENTS.md"
        return Path.home() / ".gemini" / "GEMINI.md"

    if agent == "claude":
        return Path("CLAUDE.md")
    if agent == "codex":
        return Path("AGENTS.md")
    return Path("GEMINI.md")


def _install_claude(force: bool, scope: Literal["project", "global"]) -> list[str]:
    installed_paths = [_append_agent_block(_agent_instruction_path("claude", scope), "Claude Code")]

    if scope == "global":
        return installed_paths

    claude_dir = Path(".claude")
    hooks_dir = claude_dir / "hooks"
    memory_file = claude_dir / "CLAUDE.md"
    settings_file = claude_dir / "settings.json"
    hook_file = hooks_dir / "remnant_session_start.py"

    for path in (settings_file, hook_file):
        if path.exists() and not force:
            _fail(f"{path} already exists. Use --force to overwrite.")

    hooks_dir.mkdir(parents=True, exist_ok=True)
    installed_paths.append(_append_agent_block(memory_file, "Claude Code"))
    hook_file.write_text(_claude_session_start_hook(), encoding="utf-8")
    settings_file.write_text(json.dumps(_claude_settings(), indent=2), encoding="utf-8")
    installed_paths.append(f"updated: {hook_file.resolve()}")
    installed_paths.append(f"updated: {settings_file.resolve()}")
    return installed_paths


def _append_agent_block(path: Path, agent_name: str) -> str:
    marker = f"<!-- remnant:{agent_name.lower().replace(' ', '-')} -->"
    block = f"""

{marker}
## Remnant Integration

For {agent_name}, use Remnant without copy/paste:

1. At startup, read `REMNANT.md` before touching files.
2. Use `REMNANT.md` as the local project memory map.
3. If `REMNANT.md` is missing, create it from `REMNANT.template.md`.
4. Before final response, update `REMNANT.md` with `Done`, `Failed`, `State`, `Next`, and `Blockers`.
5. Never commit `REMNANT.md`; it is local-only and ignored by Git.
6. If the user says "use remnant", search local memories with `remnant search <query>` and then read the matching `REMNANT.md`.
"""
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {path.stem}\n"
    if marker in existing:
        return f"already configured: {path.resolve()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(existing.rstrip() + block + "\n", encoding="utf-8")
    return f"updated: {path.resolve()}"


def _claude_memory_text() -> str:
    return """# Remnant Claude Code Memory

At startup, use the Remnant session context injected by the SessionStart hook.

Rules:
- Read `REMNANT.md` before touching project files.
- Use `REMNANT.md` as a compact context map, not full chat history.
- If `REMNANT.md` is missing, create it from `REMNANT.template.md`.
- Before final response, update `REMNANT.md` with `Done`, `Failed`, `State`, `Next`, and `Blockers`.
- Never store secrets, credentials, tokens, private chat text, personal data, or irrelevant logs in `REMNANT.md`.
- Never commit `REMNANT.md`; it is local-only memory.
"""


def _claude_settings() -> dict:
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/remnant_session_start.py\"",
                        }
                    ],
                },
                {
                    "matcher": "resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/remnant_session_start.py\"",
                        }
                    ],
                },
            ]
        }
    }


def _claude_session_start_hook() -> str:
    return '''from __future__ import annotations

import os
from pathlib import Path

project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
remnant_path = project_dir / "REMNANT.md"

if not remnant_path.exists():
    print("Remnant: REMNANT.md is missing. Create it from REMNANT.template.md before relying on saved context.")
    raise SystemExit(0)

content = remnant_path.read_text(encoding="utf-8")
print(f"""Remnant local context loaded from {remnant_path}.

Use this as the project memory map. Before final response, update REMNANT.md.

{content}
""")
'''


def _index_path() -> Path:
    import os

    root = Path(os.environ.get("REMNANT_HOME", Path.home() / ".remnant"))
    return root / "projects.json"


def _update_project_index(remnant_path: Path, remnant) -> None:
    index_path = _index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    data = _read_project_index(index_path)
    project_path = remnant_path.parent
    next_item = remnant.next[0] if remnant.next else ""
    project = {
        "name": remnant.project_name,
        "path": str(project_path),
        "remnant": str(remnant_path),
        "last_seen": remnant.session.date,
        "next": next_item,
    }

    projects = [item for item in data["projects"] if item.get("path") != str(project_path)]
    projects.append(project)
    projects.sort(key=lambda item: item.get("last_seen", ""), reverse=True)
    index_path.write_text(json.dumps({"projects": projects}, indent=2), encoding="utf-8")


def _read_project_index(index_path: Path | None = None) -> dict[str, list[dict[str, str]]]:
    path = index_path or _index_path()
    if not path.exists():
        return {"projects": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"projects": []}
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        return {"projects": []}
    return {"projects": [item for item in projects if isinstance(item, dict)]}


def _format_project_index(search: str | None = None) -> str:
    projects = _read_project_index()["projects"]
    if search:
        needle = search.lower()
        projects = [
            item
            for item in projects
            if needle in str(item.get("name", "")).lower()
            or needle in str(item.get("path", "")).lower()
            or needle in str(item.get("next", "")).lower()
        ]

    if not projects:
        return "No indexed Remnant projects.\n"

    lines: list[str] = []
    for item in projects:
        lines.extend(
            [
                f"Project: {item.get('name', '')}",
                f"Path: {item.get('path', '')}",
                f"REMNANT.md: {item.get('remnant', '')}",
                f"Last seen: {item.get('last_seen', '')}",
                f"Next: {item.get('next', '') or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def _format_inject(remnant) -> str:
    return "\n".join(
        [
            f"Project: {remnant.project_name}",
            f"Last session: {remnant.session.date} ({remnant.session.agent}, {remnant.session.duration}m)",
            "",
            "Done:",
            _format_plain_list(remnant.done),
            "",
            "Failed:",
            _format_plain_list(remnant.failed),
            "",
            "State:",
            _format_plain_list(remnant.state),
            "",
            "Next:",
            _format_plain_list(remnant.next),
            "",
            "Blockers:",
            _format_plain_list(remnant.blockers),
            "",
        ]
    )


def _format_plain_list(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _fail(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(1)


def _run_shell() -> None:
    typer.echo(_shell_banner())
    while True:
        try:
            raw = input("remnant > ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("")
            return

        if not raw:
            continue

        if raw in ("/exit", "exit", "quit", "/quit"):
            return

        if raw in ("/", "/help"):
            typer.echo(_shell_help())
            continue

        if not raw.startswith("/"):
            typer.echo("Use slash commands. Type / to list commands.")
            continue

        _run_shell_command(raw)


def _run_shell_command(raw: str) -> None:
    parts = shlex.split(raw[1:], posix=False)
    if not parts:
        return

    command = parts[0]
    args = parts[1:]

    try:
        if command == "install":
            if not args:
                typer.echo("Usage: /install <claude|codex|gemini|antigravity|all>")
                return
            agent = args[0]
            if agent not in {"claude", "codex", "gemini", "antigravity", "all"}:
                typer.echo("Usage: /install <claude|codex|gemini|antigravity|all>")
                return
            install(agent)  # type: ignore[arg-type]
        elif command == "init":
            init()
        elif command == "sync":
            sync()
        elif command == "status":
            status(all="--all" in args)
        elif command == "search":
            query = " ".join(args).strip()
            if not query:
                typer.echo("Usage: /search <query>")
                return
            search(query)
        elif command == "inject":
            inject()
        elif command == "capture":
            next_value = " ".join(args).strip()
            capture(next=next_value or None)
        else:
            typer.echo(f"Unknown command: /{command}. Type /help.")
    except typer.Exit:
        return


def _shell_help() -> str:
    width = max(len(command) for command, _ in SHELL_COMMANDS)
    lines = ["Commands", "--------"]
    lines.extend(f"{command.ljust(width)}  {description}" for command, description in SHELL_COMMANDS)
    return "\n".join(lines) + "\n"


def _shell_banner() -> str:
    return "\n".join(
        [
            SHELL_LOGO.strip(),
            "",
            "LOCAL MEMORY FOR AI CODING SESSIONS",
            "Type / to list commands. Type /exit to quit.",
            "",
        ]
    )


if __name__ == "__main__":
    sys.exit(app())
