from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

Agent = Literal["claude-code", "codex", "gemini-cli", "antigravity", "other"]
SectionName = Literal["Done", "Failed", "State", "Next", "Blockers"]

SECTION_NAMES: tuple[SectionName, ...] = ("Done", "Failed", "State", "Next", "Blockers")
AGENTS: set[str] = {"claude-code", "codex", "gemini-cli", "antigravity", "other"}


@dataclass(frozen=True)
class Session:
    date: str
    agent: Agent
    duration: int


@dataclass(frozen=True)
class Remnant:
    project_name: str
    session: Session
    done: list[str]
    failed: list[str]
    state: list[str]
    next: list[str]
    blockers: list[str]


def create_empty_remnant(project_name: str, agent: Agent = "codex") -> Remnant:
    return Remnant(
        project_name=project_name,
        session=Session(date=datetime.now(UTC).isoformat().replace("+00:00", "Z"), agent=agent, duration=0),
        done=[],
        failed=[],
        state=[],
        next=[],
        blockers=[],
    )


def parse_remnant_markdown(markdown: str) -> Remnant:
    lines = markdown.replace("\r\n", "\n").split("\n")
    title = next((line for line in lines if line.startswith("# Remnant ")), None)
    if title is None:
        raise ValueError("Invalid REMNANT.md: missing '# Remnant - <project-name>' title")

    project_name = _parse_title(title)
    session = _parse_session(lines)
    sections = {name: _parse_list_section(lines, name) for name in SECTION_NAMES}

    remnant = Remnant(
        project_name=project_name,
        session=session,
        done=sections["Done"],
        failed=sections["Failed"],
        state=sections["State"],
        next=sections["Next"],
        blockers=sections["Blockers"],
    )
    validate_remnant(remnant)
    return remnant


def render_remnant_markdown(remnant: Remnant) -> str:
    validate_remnant(remnant)
    return "\n".join(
        [
            f"# Remnant \u2014 {remnant.project_name}",
            "",
            "## Session",
            f"- date: {remnant.session.date}",
            f"- agent: {remnant.session.agent}",
            f"- duration: {remnant.session.duration}",
            "",
            "## Done",
            _render_list(remnant.done),
            "",
            "## Failed",
            _render_list(remnant.failed),
            "",
            "## State",
            _render_list(remnant.state),
            "",
            "## Next",
            _render_list(remnant.next),
            "",
            "## Blockers",
            _render_list(remnant.blockers),
            "",
        ]
    )


def validate_remnant(remnant: Remnant) -> None:
    if not remnant.project_name:
        raise ValueError("Invalid REMNANT.md: projectName is required")
    _validate_datetime(remnant.session.date)
    if remnant.session.agent not in AGENTS:
        raise ValueError("Invalid REMNANT.md: session.agent is invalid")
    if not isinstance(remnant.session.duration, int) or remnant.session.duration < 0:
        raise ValueError("Invalid REMNANT.md: session.duration must be a non-negative integer")


def _parse_title(title: str) -> str:
    for separator in (" — ", " - "):
        if separator in title:
            project_name = title.split(separator, 1)[1].strip()
            if project_name:
                return project_name
    raise ValueError("Invalid REMNANT.md: missing '# Remnant - <project-name>' title")


def _parse_session(lines: list[str]) -> Session:
    try:
        start = lines.index("## Session")
    except ValueError as error:
        raise ValueError("Invalid REMNANT.md: missing Session section") from error

    values: dict[str, str] = {}
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            values[key.strip()] = value.strip()

    agent = values.get("agent", "")
    if agent not in AGENTS:
        raise ValueError("Invalid REMNANT.md: session.agent is invalid")

    try:
        duration = int(values.get("duration", ""))
    except ValueError as error:
        raise ValueError("Invalid REMNANT.md: session.duration must be a non-negative integer") from error

    return Session(date=values.get("date", ""), agent=agent, duration=duration)  # type: ignore[arg-type]


def _parse_list_section(lines: list[str], name: SectionName) -> list[str]:
    heading = f"## {name}"
    try:
        start = lines.index(heading)
    except ValueError as error:
        raise ValueError(f"Invalid REMNANT.md: missing {name} section") from error

    items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("-"):
            item = line[1:].strip()
            if item:
                items.append(item)
    return items


def _render_list(items: list[str]) -> str:
    if not items:
        return "-"
    return "\n".join(f"- {item}" for item in items)


def _validate_datetime(value: str) -> None:
    if not value:
        raise ValueError("Invalid REMNANT.md: session.date is required")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError("Invalid REMNANT.md: session.date must be ISO 8601") from error
