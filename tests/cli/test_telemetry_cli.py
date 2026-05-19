"""Tests for codecarbon telemetry CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from codecarbon.cli import main as cli_main
from codecarbon.cli.telemetry_cli import normalize_telemetry_level, telemetry_app


def test_normalize_telemetry_level_accepts_valid_values():
    assert normalize_telemetry_level("MINIMAL") == "minimal"
    assert normalize_telemetry_level("disabled") == "disabled"


def test_normalize_telemetry_level_rejects_invalid():
    with pytest.raises(Exception):
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


def test_telemetry_show_reports_stored_level():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / ".codecarbon.config"
        config_path.write_text("[codecarbon]\ntelemetry_level = extensive\n")
        result = runner.invoke(
            telemetry_app,
            ["show", "--config", str(config_path)],
        )
        assert result.exit_code == 0
        assert "extensive" in result.output
        assert "Explicitly configured: True" in result.output


def test_telemetry_show_merged_matches_tracker_precedence():
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
            result = runner.invoke(telemetry_app, ["show"])
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
