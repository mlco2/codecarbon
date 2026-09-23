from codecarbon.cli.tracker_options import extra_tracker_param_names, iter_tracker_cli_params


def test_generated_options_include_pue_and_wue():
    names = extra_tracker_param_names()
    assert "pue" in names
    assert "wue" in names
    assert "measure_power_secs" not in names
    assert "logging_logger" not in names


def test_generated_option_types():
    types = {name: cli_type for name, cli_type, _ in iter_tracker_cli_params()}
    assert types["pue"] is float
    assert types["wue"] is float
    assert types["project_name"] is str
    assert types["allow_multiple_runs"] is bool


def test_monitor_forwards_generated_tracker_options(monkeypatch):
    import codecarbon.cli.main as cli_main
    from typer.testing import CliRunner

    calls = {"kwargs": None}

    class FakeOfflineTracker:
        def __init__(self, **kwargs):
            calls["kwargs"] = kwargs
            self._another_instance_already_running = True

        def start(self):
            return None

        def stop(self):
            return None

    monkeypatch.setattr(
        "codecarbon.emissions_tracker.OfflineEmissionsTracker", FakeOfflineTracker
    )
    monkeypatch.setattr(cli_main.signal, "signal", lambda *args, **kwargs: None)

    result = CliRunner().invoke(
        cli_main.codecarbon,
        [
            "monitor",
            "--offline",
            "--country-iso-code",
            "FRA",
            "--pue",
            "1.4",
            "--wue",
            "0.5",
            "--project-name",
            "cli-monitor",
        ],
    )
    assert result.exit_code == 0, result.output
    assert calls["kwargs"]["pue"] == 1.4
    assert calls["kwargs"]["wue"] == 0.5
    assert calls["kwargs"]["project_name"] == "cli-monitor"


def test_monitor_help_lists_generated_package_options():
    import codecarbon.cli.main as cli_main
    from typer.testing import CliRunner

    result = CliRunner().invoke(cli_main.codecarbon, ["monitor", "--help"])
    assert result.exit_code == 0
    assert "--pue" in result.output
    assert "--wue" in result.output
    assert "--force-cpu-power" in result.output
