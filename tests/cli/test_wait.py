from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import typer

from codecarbon.cli import wait as wait_module
from codecarbon.core.intensity_forecast import Forecast, IntensityPoint


def _forecast(values, start):
    return Forecast(
        zone="FR",
        points=[
            IntensityPoint(at=start + timedelta(hours=i), g_co2e_per_kwh=v)
            for i, v in enumerate(values)
        ],
        source="test",
        fetched_at=start,
    )


@pytest.fixture
def no_network(monkeypatch):
    """Never let the wait command reach geolocation or the intensity API."""
    monkeypatch.setattr(
        "codecarbon.external.geography.GeoMetadata.from_geo_js",
        classmethod(lambda cls, url: SimpleNamespace()),
    )
    monkeypatch.setattr(
        "codecarbon.core.config.get_hierarchical_config",
        lambda: {"electricitymaps_api_token": "tok"},
    )


def _patch_forecast(monkeypatch, values):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "codecarbon.core.intensity_forecast.get_forecast",
        lambda geo, **kwargs: _forecast(values, now),
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("90m", timedelta(minutes=90)),
        ("2h", timedelta(hours=2)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        ("45s", timedelta(seconds=45)),
        ("3600", timedelta(hours=1)),
    ],
)
def test_parse_duration(value, expected):
    assert wait_module.parse_duration(value) == expected


@pytest.mark.parametrize("value", ["", "soon", "2 hours", "h", "-1h"])
def test_parse_duration_rejects_garbage(value):
    with pytest.raises(ValueError):
        wait_module.parse_duration(value)


def test_dry_run_prints_recommendation_and_exits(monkeypatch, capsys, no_network):
    _patch_forecast(monkeypatch, [300, 300, 100, 100, 300])
    slept = []
    monkeypatch.setattr(wait_module.time, "sleep", lambda s: slept.append(s))

    with pytest.raises(typer.Exit) as exc:
        wait_module.wait_for_green_window(
            SimpleNamespace(args=[]), duration="2h", deadline="6h", dry_run=True
        )

    assert exc.value.exit_code == 0
    assert slept == []
    out = capsys.readouterr().out
    assert "Best start" in out
    assert "saves ~67%" in out


def test_invalid_duration_exits_with_error(monkeypatch, capsys, no_network):
    with pytest.raises(typer.Exit) as exc:
        wait_module.wait_for_green_window(
            SimpleNamespace(args=[]), duration="whenever", dry_run=True
        )
    assert exc.value.exit_code == 1


def test_no_forecast_runs_now(monkeypatch, capsys, no_network):
    monkeypatch.setattr(
        "codecarbon.core.intensity_forecast.get_forecast", lambda geo, **kwargs: None
    )
    slept = []
    monkeypatch.setattr(wait_module.time, "sleep", lambda s: slept.append(s))
    called = {}
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor",
        lambda ctx, **kwargs: called.setdefault("args", list(ctx.args)),
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=["wait", "--", "python", "train.py"])
    )

    assert slept == []
    assert called["args"] == ["--", "python", "train.py"]
    assert "no forecast available" in capsys.readouterr().out


def test_threshold_short_circuits_the_wait(monkeypatch, capsys, no_network):
    _patch_forecast(monkeypatch, [120, 300, 50, 50])
    slept = []
    monkeypatch.setattr(wait_module.time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor", lambda ctx, **kwargs: None
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=["python", "train.py"]),
        duration="1h",
        deadline="6h",
        threshold=150,
    )

    assert slept == []
    assert "running now" in capsys.readouterr().out


def test_no_second_call_for_the_current_intensity(monkeypatch, capsys, no_network):
    # The first forecast point is the "now" value: fetching /latest as well
    # would be a second HTTP call just to print a percentage.
    _patch_forecast(monkeypatch, [120, 300, 50, 50])
    monkeypatch.setattr(
        "codecarbon.core.electricitymaps_api.get_carbon_intensity",
        lambda *a, **k: pytest.fail("second live call"),
    )
    monkeypatch.setattr(wait_module.time, "sleep", lambda s: pytest.fail("slept"))
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor", lambda ctx, **kwargs: None
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=[]), duration="1h", deadline="6h", threshold=150
    )

    assert "running now" in capsys.readouterr().out


def test_finish_by_bounds_the_end_not_the_start(monkeypatch, no_network):
    # Trough at +4h, but the job must be done by +3h, so only a start at or
    # before +2h is acceptable: the cheapest of those is +1h.
    _patch_forecast(monkeypatch, [300, 100, 200, 200, 10, 10])
    slept = []
    monkeypatch.setattr(wait_module.time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor", lambda ctx, **kwargs: None
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=[]), duration="1h", finish_by="3h"
    )

    assert len(slept) == 1
    assert 3600 - 60 < slept[0] <= 3600


def test_finish_by_shorter_than_duration_is_rejected(monkeypatch, capsys, no_network):
    with pytest.raises(typer.Exit):
        wait_module.wait_for_green_window(
            SimpleNamespace(args=[]), duration="4h", finish_by="1h"
        )


def test_only_the_leading_subcommand_name_is_stripped(monkeypatch, no_network):
    _patch_forecast(monkeypatch, [100, 300, 300])
    called = {}
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor",
        lambda ctx, **kwargs: called.setdefault("args", list(ctx.args)),
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=["wait", "--", "make", "wait"]), duration="1h"
    )

    assert called["args"] == ["--", "make", "wait"]


def test_sleeps_until_the_green_window_then_delegates(monkeypatch, no_network):
    _patch_forecast(monkeypatch, [300, 300, 100, 100, 300])
    slept = []
    monkeypatch.setattr(wait_module.time, "sleep", lambda s: slept.append(s))
    called = {}
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor",
        lambda ctx, **kwargs: called.update(kwargs, args=list(ctx.args)),
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=["wait", "python", "train.py"]),
        duration="2h",
        deadline="6h",
        measure_power_secs=15,
    )

    assert len(slept) == 1
    assert 2 * 3600 - 60 < slept[0] <= 2 * 3600
    assert called["args"] == ["python", "train.py"]
    assert called["measure_power_secs"] == 15


def test_keyboard_interrupt_during_wait_runs_immediately(monkeypatch, no_network):
    _patch_forecast(monkeypatch, [300, 300, 100, 100, 300])

    def _interrupt(seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(wait_module.time, "sleep", _interrupt)
    called = {}
    monkeypatch.setattr(
        "codecarbon.cli.monitor.run_and_monitor",
        lambda ctx, **kwargs: called.setdefault("ran", True),
    )

    wait_module.wait_for_green_window(
        SimpleNamespace(args=["python", "train.py"]), duration="2h", deadline="6h"
    )

    assert called["ran"] is True
