from __future__ import annotations

import subprocess
from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from remnant_cli.main import app
from remnant_cli.schema import create_empty_remnant, parse_remnant_markdown, render_remnant_markdown

runner = CliRunner()


def test_schema_parses_rendered_markdown() -> None:
    source = create_empty_remnant("example")
    parsed = parse_remnant_markdown(render_remnant_markdown(source))

    assert parsed.project_name == "example"
    assert parsed.session.agent == "codex"


def test_init_creates_valid_markdown(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"], catch_exceptions=False, env={}, prog_name="remnant")

    assert result.exit_code == 0
    parsed = parse_remnant_markdown((tmp_path / "REMNANT.md").read_text(encoding="utf-8"))
    assert parsed.project_name.startswith("test_init_creates_valid")
    assert (tmp_path / ".remnant-home" / "projects.json").exists()


def test_capture_includes_git_derived_state(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@remnant.local")
    _git(tmp_path, "config", "user.name", "Remnant Test")
    _git(tmp_path, "checkout", "-b", "feature/test")
    (tmp_path / "tracked.txt").write_text("content", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    result = runner.invoke(app, ["capture", "--next", "continue CLI work"], catch_exceptions=False)
    parsed = parse_remnant_markdown((tmp_path / "REMNANT.md").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert "branch: feature/test" in parsed.state
    assert "git status:" in parsed.state
    # Staged file detected.
    assert any("tracked.txt" in item for item in parsed.state)
    assert "continue CLI work" in (tmp_path / ".remnant-home" / "projects.json").read_text(encoding="utf-8")


def test_init_force_overwrites_existing_remnant(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    result = runner.invoke(app, ["init", "--force"], catch_exceptions=False)

    assert result.exit_code == 0


def test_capture_without_next_on_empty_remnant_fails_clearly(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    result = runner.invoke(app, ["capture"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "--next" in result.stderr


def test_inject_fails_clearly_when_remnant_is_missing(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["inject"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "REMNANT.md not found" in result.stderr


def test_sync_validates_and_prints_placeholder(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    result = runner.invoke(app, ["sync"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.stdout == "backend sync not implemented\n"


def test_status_all_lists_indexed_projects(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    runner.invoke(app, ["capture", "--next", "resume indexed project"], catch_exceptions=False)
    result = runner.invoke(app, ["status", "--all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Project:" in result.stdout
    assert "REMNANT.md:" in result.stdout
    assert "resume indexed project" in result.stdout


def test_status_search_filters_indexed_projects(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    runner.invoke(app, ["capture", "--next", "rewrite install docs"], catch_exceptions=False)
    result = runner.invoke(app, ["status", "--search", "install"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "rewrite install docs" in result.stdout


def test_search_lists_matching_indexed_projects(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REMNANT_HOME", str(tmp_path / ".remnant-home"))
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    runner.invoke(app, ["capture", "--next", "continue backend sync"], catch_exceptions=False)
    result = runner.invoke(app, ["search", "backend"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "continue backend sync" in result.stdout
    assert "REMNANT.md:" in result.stdout


def test_install_claude_creates_project_integration(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "claude"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "CLAUDE.md").exists()
    assert (tmp_path / ".claude" / "settings.json").exists()
    assert (tmp_path / ".claude" / "hooks" / "remnant_session_start.py").exists()
    settings = (tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert "SessionStart" in settings
    assert "remnant_session_start.py" in settings


def test_install_claude_requires_force_for_existing_files(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install", "claude"], catch_exceptions=False)
    result = runner.invoke(app, ["install", "claude"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "--force" in result.stderr


def test_status_fails_clearly_when_remnant_is_invalid(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    (tmp_path / "REMNANT.md").write_text("invalid", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["status"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "Invalid REMNANT.md" in result.stderr


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
