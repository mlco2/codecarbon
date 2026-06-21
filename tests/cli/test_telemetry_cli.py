"""Tests for codecarbon telemetry CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from codecarbon.cli import main as cli_main
from codecarbon.cli.telemetry_cli import (
    normalize_telemetry_level,
    pick_config_path_interactive,
    resolve_config_path,
    telemetry_app,
    write_telemetry_level,
)


def test_normalize_telemetry_level_accepts_valid_values():
    assert normalize_telemetry_level("MINIMAL") == "minimal"
    assert normalize_telemetry_level("disabled") == "disabled"


def test_normalize_telemetry_level_rejects_invalid():
    with pytest.raises(typer.BadParameter):
        normalize_telemetry_level("bogus")


def test_telemetry_set_writes_config():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / ".codecarbon.config"
        result = runner.invoke(
            telemetry_app,
            ["set", "disabled", "--config", str(config_path)],
        )
        assert result.exit_code == 0
        assert "telemetry_level = disabled" in result.output
        content = config_path.read_text()
        assert "telemetry_level = disabled" in content


def test_telemetry_status_reports_stored_level():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / ".codecarbon.config"
        config_path.write_text("[codecarbon]\ntelemetry_level = extensive\n")
        result = runner.invoke(
            telemetry_app,
            ["status", "--config", str(config_path)],
        )
        assert result.exit_code == 0
        assert "extensive" in result.output
        assert "Explicitly configured: True" in result.output


def test_telemetry_status_merged_matches_tracker_precedence():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        global_path = Path(tmp) / "global.config"
        local_path = Path(tmp) / "local.config"
        global_path.write_text("[codecarbon]\ntelemetry_level = minimal\n")
        local_path.write_text("[codecarbon]\ntelemetry_level = disabled\n")
        with patch(
            "codecarbon.core.config._config_file_paths",
            return_value=(str(global_path), str(local_path)),
        ):
            result = runner.invoke(telemetry_app, ["status"])
        assert result.exit_code == 0
        assert "Resolved tier: disabled" in result.output
        assert "merged" in result.output


def test_monitor_passes_telemetry_level_override(monkeypatch):
    from codecarbon.cli import monitor as monitor_module

    captured = {}

    class FakeTracker:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self._conf = {"output_file": "emissions.csv"}

        def start(self):
            return None

        def stop(self):
            return 0.0

    monkeypatch.setattr(monitor_module, "EmissionsTracker", FakeTracker)

    runner = CliRunner()
    result = runner.invoke(
        cli_main.codecarbon,
        [
            "monitor",
            "--no-api",
            "--telemetry-level",
            "disabled",
            "--",
            "echo",
            "ok",
        ],
    )
    assert result.exit_code == 0
    assert captured.get("telemetry_level") == "disabled"


def test_monitor_rejects_invalid_telemetry_level():
    runner = CliRunner()
    result = runner.invoke(
        cli_main.codecarbon,
        ["monitor", "--telemetry-level", "invalid"],
    )
    assert result.exit_code != 0


def test_telemetry_status_missing_config_file():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing.config"
        result = runner.invoke(
            telemetry_app,
            ["status", "--config", str(missing)],
        )
    assert result.exit_code == 0
    assert "Config file not found" in result.output
    assert "not explicit" in result.output


def test_telemetry_status_shows_implicit_warning():
    runner = CliRunner()
    with patch(
        "codecarbon.cli.telemetry_cli.get_config_file_settings",
        return_value={},
    ):
        with patch(
            "codecarbon.cli.telemetry_cli.get_hierarchical_config",
            return_value={},
        ):
            result = runner.invoke(telemetry_app, ["status"])
    assert "Explicitly configured: False" in result.output
    assert "Minimal telemetry will be sent" in result.output


def test_resolve_config_path_creates_explicit_file():
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "custom.config"
        resolved = resolve_config_path(config_path, create=True)
        assert resolved == config_path.resolve()
        assert config_path.exists()


def test_resolve_config_path_prefers_local_config(tmp_path, monkeypatch):
    local_path = tmp_path / ".codecarbon.config"
    local_path.write_text("[codecarbon]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert resolve_config_path(None) == local_path.resolve()


def test_resolve_config_path_uses_global_when_local_missing(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    global_path = home / ".codecarbon.config"
    global_path.write_text("[codecarbon]\n", encoding="utf-8")
    workdir = tmp_path / "work"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    monkeypatch.setattr(Path, "home", lambda: home)
    assert resolve_config_path(None) == global_path.resolve()


def test_write_telemetry_level_creates_missing_file(tmp_path):
    config_path = tmp_path / "nested" / ".codecarbon.config"
    write_telemetry_level(config_path, "minimal")
    assert config_path.exists()
    assert "telemetry_level = minimal" in config_path.read_text()


def test_pick_config_path_interactive_create_new():
    with patch("codecarbon.cli.telemetry_cli.questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = "Create new config file"
        with patch(
            "codecarbon.cli.telemetry_cli.create_new_config_file",
            return_value=Path("/tmp/new.config"),
        ) as mock_create:
            path = pick_config_path_interactive()
    mock_create.assert_called_once()
    assert path == Path("/tmp/new.config")


def test_resolve_config_path_creates_local_in_cwd(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setattr(Path, "home", lambda: home)
    resolved = resolve_config_path(None, create=True)
    assert resolved == (work / ".codecarbon.config").resolve()
    assert resolved.exists()


def test_pick_config_path_lists_existing_configs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    global_path = home / ".codecarbon.config"
    global_path.write_text("[codecarbon]\n", encoding="utf-8")
    work = tmp_path / "work"
    work.mkdir()
    local_path = work / ".codecarbon.config"
    local_path.write_text("[codecarbon]\n", encoding="utf-8")
    monkeypatch.chdir(work)
    monkeypatch.setattr(Path, "home", lambda: home)
    with patch("codecarbon.cli.telemetry_cli.questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = str(local_path)
        path = pick_config_path_interactive()
    assert path == local_path.resolve()


def test_telemetry_default_command_runs_interactive_wizard(tmp_path):
    config_path = tmp_path / ".codecarbon.config"
    config_path.write_text("[codecarbon]\n", encoding="utf-8")
    runner = CliRunner()
    with patch("codecarbon.cli.telemetry_cli.questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = "disabled"
        result = runner.invoke(telemetry_app, ["--config", str(config_path)])
    assert result.exit_code == 0
    assert "telemetry_level = disabled" in config_path.read_text()


def test_telemetry_interactive_exits_when_selection_cancelled(tmp_path):
    config_path = tmp_path / ".codecarbon.config"
    config_path.write_text("[codecarbon]\n", encoding="utf-8")
    runner = CliRunner()
    with patch("codecarbon.cli.telemetry_cli.questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = None
        result = runner.invoke(telemetry_app, ["--config", str(config_path)])
    assert result.exit_code == 0
    assert "telemetry_level" not in config_path.read_text()


def test_telemetry_interactive_prompts_for_config_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    select = MagicMock()
    select.ask.return_value = "minimal"
    with patch(
        "codecarbon.cli.telemetry_cli.pick_config_path_interactive",
        return_value=tmp_path / ".codecarbon.config",
    ):
        with patch(
            "codecarbon.cli.telemetry_cli.questionary.select", return_value=select
        ):
            result = runner.invoke(telemetry_app, [])
    config_path = tmp_path / ".codecarbon.config"
    assert result.exit_code == 0
    assert config_path.exists()
    assert "telemetry_level = minimal" in config_path.read_text()
