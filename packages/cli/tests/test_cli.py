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


def test_no_command_opens_interactive_shell_and_exits() -> None:
    result = runner.invoke(app, input="/help\n/exit\n", catch_exceptions=False)

    assert result.exit_code == 0
    assert "Remnant CLI" in result.stdout
    assert "/install <claude|codex|gemini|antigravity|all>" in result.stdout


def test_interactive_install_codex(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, input="/install codex\n/exit\n", catch_exceptions=False)

    assert result.exit_code == 0
    assert (tmp_path / "AGENTS.md").exists()


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


def test_init_refuses_default_file_in_home(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "home folder" in result.stderr
    assert not (tmp_path / "REMNANT.md").exists()


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
    (tmp_path / "CLAUDE.md").write_text("# Existing Claude\n", encoding="utf-8")
    result = runner.invoke(app, ["install", "claude"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "CLAUDE.md").exists()
    assert (tmp_path / ".claude" / "settings.json").exists()
    assert (tmp_path / ".claude" / "hooks" / "remnant_session_start.py").exists()
    settings = (tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert "SessionStart" in settings
    assert "remnant_session_start.py" in settings
    root_claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "# Existing Claude" in root_claude
    assert "## Remnant Integration" in root_claude


def test_install_claude_requires_force_for_existing_files(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["install", "claude"], catch_exceptions=False)
    result = runner.invoke(app, ["install", "claude"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "--force" in result.stderr


def test_install_codex_appends_agents_md(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Existing Agents\n", encoding="utf-8")
    result = runner.invoke(app, ["install", "codex"], catch_exceptions=False)
    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert "# Existing Agents" in content
    assert "For Codex" in content
    assert "## Remnant Integration" in content


def test_install_gemini_appends_gemini_md(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "GEMINI.md").write_text("# Existing Gemini\n", encoding="utf-8")
    result = runner.invoke(app, ["install", "gemini"], catch_exceptions=False)
    content = (tmp_path / "GEMINI.md").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert "# Existing Gemini" in content
    assert "For Gemini CLI" in content
    assert "## Remnant Integration" in content


def test_install_all_appends_without_duplicate_blocks(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "all"], catch_exceptions=False)
    rerun = runner.invoke(app, ["install", "all", "--force"], catch_exceptions=False)
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert rerun.exit_code == 0
    assert agents.count("For Codex") == 1
    assert agents.count("For Google Antigravity") == 1


def test_install_all_from_home_uses_global_agent_dirs(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".gemini").mkdir()
    (tmp_path / ".codex" / "AGENTS.md").write_text("# Existing Global Codex\n\nKeep this.\n", encoding="utf-8")
    (tmp_path / ".claude" / "CLAUDE.md").write_text("# Existing Global Claude\n\nKeep this.\n", encoding="utf-8")
    (tmp_path / ".gemini" / "GEMINI.md").write_text("# Existing Global Gemini\n\nKeep this.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "all"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Keep this." in (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Keep this." in (tmp_path / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep this." in (tmp_path / ".gemini" / "GEMINI.md").read_text(encoding="utf-8")
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / "GEMINI.md").exists()


def test_install_global_scope_uses_global_agent_dirs(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["install", "codex", "--scope", "global"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (home / ".codex" / "AGENTS.md").exists()
    assert not (project / "AGENTS.md").exists()


def test_status_fails_clearly_when_remnant_is_invalid(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    (tmp_path / "REMNANT.md").write_text("invalid", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["status"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "Invalid REMNANT.md" in result.stderr


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
