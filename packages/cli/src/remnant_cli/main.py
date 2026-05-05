from __future__ import annotations

import subprocess
import sys
import json
from dataclasses import replace
from pathlib import Path
from typing import Annotated

import typer

from remnant_cli.schema import (
    Agent,
    create_empty_remnant,
    parse_remnant_markdown,
    render_remnant_markdown,
    validate_remnant,
)

app = typer.Typer(help="Persist AI session context across coding sessions.")
DEFAULT_FILE = "REMNANT.md"


@app.command()
def init(
    file: Annotated[str, typer.Option("--file", help="REMNANT.md path")] = DEFAULT_FILE,
    force: Annotated[bool, typer.Option("--force", help="overwrite existing REMNANT.md")] = False,
) -> None:
    """Init Remnant in current repo."""
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


if __name__ == "__main__":
    sys.exit(app())
