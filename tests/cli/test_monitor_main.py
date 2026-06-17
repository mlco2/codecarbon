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
