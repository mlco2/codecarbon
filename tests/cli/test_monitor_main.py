from types import SimpleNamespace
from unittest.mock import patch

import pytest
import typer

from codecarbon.cli import monitor_main


def test_monitor_main_delegates_command_to_run_and_monitor():
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["args"] = list(ctx.args)
        captured["offline"] = offline
        captured["kwargs"] = kwargs

    ctx = SimpleNamespace(args=["echo", "hello"])
    with patch.object(monitor_main, "run_and_monitor", fake_run_and_monitor):
        monitor_main.monitor(
            ctx=ctx,
            offline=True,
            country_iso_code="FRA",
            log_level="error",
        )

    assert captured["args"] == ["echo", "hello"]
    assert captured["offline"] is True
    assert captured["kwargs"]["country_iso_code"] == "FRA"
    assert captured["kwargs"]["log_level"] == "error"


def test_monitor_main_requires_command():
    ctx = SimpleNamespace(args=[])
    with pytest.raises(typer.Exit) as exc_info:
        monitor_main.monitor(ctx=ctx, offline=True, country_iso_code="FRA")
    assert exc_info.value.exit_code == 1


def test_monitor_main_offline_requires_country_iso_code():
    ctx = SimpleNamespace(args=["echo", "hi"])
    with pytest.raises(typer.Exit) as exc_info:
        monitor_main.monitor(ctx=ctx, offline=True)
    assert exc_info.value.exit_code == 1


def test_monitor_main_online_requires_experiment_id():
    ctx = SimpleNamespace(args=["echo", "hi"])
    with patch("codecarbon.cli.cli_utils.get_existing_exp_id", return_value=None):
        with pytest.raises(typer.Exit) as exc_info:
            monitor_main.monitor(ctx=ctx, offline=False, api=True)
    assert exc_info.value.exit_code == 1


def test_monitor_main_online_with_experiment_id():
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["offline"] = offline
        captured["kwargs"] = kwargs

    ctx = SimpleNamespace(args=["echo", "hi"])
    with (
        patch("codecarbon.cli.cli_utils.get_existing_exp_id", return_value="exp-123"),
        patch.object(monitor_main, "run_and_monitor", fake_run_and_monitor),
    ):
        monitor_main.monitor(ctx=ctx, offline=False, api=True)

    assert captured["offline"] is False
    assert captured["kwargs"]["save_to_api"] is True


def test_monitor_main_entrypoint():
    with patch.object(monitor_main, "app") as mock_app:
        monitor_main.main()
    mock_app.assert_called_once_with(prog_name="codecarbon-monitor")
