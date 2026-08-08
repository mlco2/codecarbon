"""Tests for the CodeCarbon CLI main function."""

from types import SimpleNamespace

import pytest
import requests
import typer
from typer.testing import CliRunner

from codecarbon.cli import main as cli_main


class FakeApiClient:
    def __init__(self, endpoint_url=None):
        self.endpoint_url = endpoint_url
        self.token = None

    def set_access_token(self, token):
        self.token = token

    def get_list_organizations(self):
        return [{"id": "1", "name": "fake-org"}]


def fake_get_access_token():
    return "fake-token"


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["--version"])
    assert result.exit_code == 0
    assert cli_main.__app_name__ in result.output
    assert str(cli_main.__version__) in result.output


def test_api_get_calls_api_and_prints(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", FakeApiClient)
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", fake_get_access_token)

    result = runner.invoke(cli_main.codecarbon, ["test-api"])
    assert result.exit_code == 0
    assert "fake-org" in result.output


def test_api_get_prints_friendly_error_on_api_failure(monkeypatch):
    class FailingApiClient(FakeApiClient):
        def get_list_organizations(self):
            raise requests.exceptions.HTTPError("401 Unauthorized")

    runner = CliRunner()
    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", FailingApiClient)
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", fake_get_access_token)

    result = runner.invoke(cli_main.codecarbon, ["test-api"])
    assert result.exit_code == 1
    assert "API request failed" in result.output
    assert "401 Unauthorized" in result.output


def test_api_get_uses_get_api_endpoint(monkeypatch):
    call_info = {}

    class CustomApiClient(FakeApiClient):
        def __init__(self, endpoint_url=None):
            call_info["endpoint_url"] = endpoint_url
            super().__init__(endpoint_url=endpoint_url)

    runner = CliRunner()
    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", CustomApiClient)
    monkeypatch.setattr(
        cli_main, "get_api_endpoint", lambda: "https://custom.codecarbon.io"
    )
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", fake_get_access_token)

    result = runner.invoke(cli_main.codecarbon, ["test-api"])
    assert result.exit_code == 0
    assert call_info["endpoint_url"] == "https://custom.codecarbon.io"


def test_monitor_offline_requires_country_iso_code():
    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["monitor", "--offline"])
    assert result.exit_code != 0
    assert "Country ISO code is required for offline mode" in result.output


def test_detect_monkeypatched_tracker(monkeypatch):
    class FakeTracker:
        def __init__(self, save_to_file=False, **kwargs):
            pass

        def get_detected_hardware(self):
            return {
                "ram_total_size": 8.0,
                "cpu_count": 4,
                "cpu_physical_count": 2,
                "cpu_model": "Fake CPU",
                "gpu_count": 1,
                "gpu_model": "Fake GPU",
                "gpu_ids": None,
            }

    monkeypatch.setattr("codecarbon.emissions_tracker.EmissionsTracker", FakeTracker)
    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["detect"])
    assert result.exit_code == 0
    assert "Detected Hardware" in result.output
    assert "Fake CPU" in result.output


def test_monitor_run_and_monitor(monkeypatch):
    runner = CliRunner()

    # Test with a simple command
    result = runner.invoke(
        cli_main.codecarbon, ["monitor", "--no-api", "--", "echo", "Hello, World!"]
    )
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def test_show_config_handles_access_token_errors(monkeypatch, tmp_path, capsys):
    class FakeApiClient:
        def __init__(self, endpoint_url=None):
            self.endpoint_url = endpoint_url

        def set_access_token(self, token):
            self.token = token

    def fake_get_access_token():
        raise ValueError("Not able to retrieve the access token, please run login.")

    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", FakeApiClient)
    monkeypatch.setattr(
        cli_main,
        "get_config",
        lambda path: {
            "api_endpoint": "https://api.codecarbon.io",
            "organization_id": "org-id",
            "project_id": "project-id",
            "experiment_id": "experiment-id",
        },
    )
    monkeypatch.setattr(
        cli_main, "get_api_endpoint", lambda path: "https://api.codecarbon.io"
    )
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", fake_get_access_token)

    cli_main.show_config(tmp_path / ".codecarbon.config")
    captured = capsys.readouterr()
    assert "Could not validate remote configuration details" in captured.out
    assert "Not able to retrieve the access token" in captured.out


def test_main_exits_with_error_when_command_raises(monkeypatch, capsys):
    def fake_cli():
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_main, "codecarbon", fake_cli)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "Error:" in captured.out
    assert "boom" in captured.out


def test_login_calls_authorize_and_auth_check(monkeypatch):
    calls = {"authorize": 0, "set_token": None, "check_auth": 0, "endpoint_url": None}

    class FakeApiClient:
        def __init__(self, endpoint_url=None):
            calls["endpoint_url"] = endpoint_url

        def set_access_token(self, token):
            calls["set_token"] = token

        def check_auth(self):
            calls["check_auth"] += 1

    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", FakeApiClient)
    monkeypatch.setattr(
        "codecarbon.cli.auth.authorize",
        lambda: calls.__setitem__("authorize", calls["authorize"] + 1),
    )
    monkeypatch.setattr(
        cli_main, "get_api_endpoint", lambda: "https://custom-login.codecarbon.io"
    )
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", lambda: "login-token")

    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["login"])
    assert result.exit_code == 0
    assert calls["authorize"] == 1
    assert calls["set_token"] == "login-token"
    assert calls["check_auth"] == 1
    assert calls["endpoint_url"] == "https://custom-login.codecarbon.io"


def test_login_prints_friendly_error_on_auth_failure(monkeypatch):
    class FailingApiClient:
        def __init__(self, endpoint_url=None):
            pass

        def set_access_token(self, token):
            pass

        def check_auth(self):
            raise requests.exceptions.HTTPError("403 Forbidden")

    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", FailingApiClient)
    monkeypatch.setattr("codecarbon.cli.auth.authorize", lambda: None)
    monkeypatch.setattr(
        cli_main, "get_api_endpoint", lambda: "https://api.codecarbon.io"
    )
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", lambda: "bad-token")

    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["login"])
    assert result.exit_code == 1
    assert "Authentication check failed" in result.output
    assert "403 Forbidden" in result.output


def test_get_api_key_uses_bearer_token(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"token": "project-api-token"}

    def fake_post(url, json, headers):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", lambda: "access-token")
    monkeypatch.setattr("requests.post", fake_post)

    token = cli_main.get_api_key("proj-123")
    assert token == "project-api-token"
    assert captured["url"].endswith("/projects/proj-123/api-tokens")
    assert captured["json"]["project_id"] == "proj-123"
    assert captured["headers"]["Authorization"] == "Bearer access-token"


def test_get_api_key_raises_on_http_error(monkeypatch):
    class FailingResponse:
        def raise_for_status(self):
            raise requests.exceptions.HTTPError("403 Forbidden")

        def json(self):  # pragma: no cover - must not be reached
            raise AssertionError("json() should not be called on a failed response")

    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", lambda: "access-token")
    monkeypatch.setattr("requests.post", lambda url, json, headers: FailingResponse())

    with pytest.raises(requests.exceptions.HTTPError):
        cli_main.get_api_key("proj-123")


def test_api_call_prints_friendly_error_and_exits():
    def failing():
        raise requests.exceptions.HTTPError("500 Server Error")

    with pytest.raises(typer.Exit) as exc_info:
        cli_main._api_call("Could not do the thing", failing)
    assert exc_info.value.exit_code == 1


def test_api_call_returns_result_and_forwards_arguments():
    captured = {}

    def succeeding(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return "ok"

    assert cli_main._api_call("unused", succeeding, "org-1", name="test") == "ok"
    assert captured["args"] == ("org-1",)
    assert captured["kwargs"] == {"name": "test"}


def test_get_token_command_prints_token(monkeypatch):
    monkeypatch.setattr(cli_main, "get_api_key", lambda project_id: "abc123")
    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["get-token", "proj-id"])
    assert result.exit_code == 0
    assert "Your token: abc123" in result.output


def test_show_config_prints_missing_project_and_experiment(
    monkeypatch, tmp_path, capsys
):
    class FakeApiClient:
        def __init__(self, endpoint_url=None):
            self.endpoint_url = endpoint_url

        def set_access_token(self, token):
            self.token = token

        def get_organization(self, organization_id):
            return {"id": organization_id}

        def get_project(self, project_id):
            return {"id": project_id}

        def get_experiment(self, experiment_id):
            return {"id": experiment_id}

    monkeypatch.setattr("codecarbon.core.api_client.ApiClient", FakeApiClient)
    monkeypatch.setattr("codecarbon.cli.auth.get_access_token", lambda: "fake-token")
    monkeypatch.setattr(
        cli_main, "get_api_endpoint", lambda path: "https://api.codecarbon.io"
    )

    monkeypatch.setattr(
        cli_main,
        "get_config",
        lambda path: {
            "api_endpoint": "https://api.codecarbon.io",
            "organization_id": "org-id",
        },
    )
    cli_main.show_config(tmp_path / ".codecarbon.config")
    captured = capsys.readouterr()
    assert "No project_id in config" in captured.out

    monkeypatch.setattr(
        cli_main,
        "get_config",
        lambda path: {
            "api_endpoint": "https://api.codecarbon.io",
            "organization_id": "org-id",
            "project_id": "project-id",
        },
    )
    cli_main.show_config(tmp_path / ".codecarbon.config")
    captured = capsys.readouterr()
    assert "No experiment_id in config" in captured.out


def test_monitor_online_requires_experiment_id(monkeypatch):
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: None)
    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["monitor"])
    assert result.exit_code == 1
    assert "No experiment id" in result.output


def test_monitor_offline_initializes_offline_tracker(monkeypatch):
    calls = {"kwargs": None, "started": 0}

    class FakeOfflineTracker:
        def __init__(self, **kwargs):
            calls["kwargs"] = kwargs
            self._another_instance_already_running = True

        def start(self):
            calls["started"] += 1

        def stop(self):
            return None

    monkeypatch.setattr(
        "codecarbon.emissions_tracker.OfflineEmissionsTracker", FakeOfflineTracker
    )
    monkeypatch.setattr(cli_main.signal, "signal", lambda *args, **kwargs: None)

    runner = CliRunner()
    result = runner.invoke(
        cli_main.codecarbon,
        ["monitor", "--offline", "--country-iso-code", "FRA", "--region", "IDF"],
    )
    assert result.exit_code == 0
    assert calls["started"] == 1
    assert calls["kwargs"]["country_iso_code"] == "FRA"
    assert calls["kwargs"]["region"] == "IDF"


def test_monitor_forwards_explicit_tracker_options(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["args"] = list(ctx.args)
        captured["offline"] = offline
        captured["kwargs"] = kwargs

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)

    runner = CliRunner()
    result = runner.invoke(
        cli_main.codecarbon,
        [
            "monitor",
            "--offline",
            "--country-iso-code",
            "FRA",
            "--project-name",
            "cli-project",
            "--api-endpoint",
            "https://api.example.com",
            "--api-key",
            "secret",
            "--output-dir",
            "/tmp/emissions",
            "--output-file",
            "custom.csv",
            "--output-methods",
            "csv,logger",
            "--no-save-to-file",
            "--save-to-logger",
            "--save-to-prometheus",
            "--no-save-to-logfire",
            "--prometheus-url",
            "http://localhost:9091",
            "--gpu-ids",
            "0,2",
            "--emissions-endpoint",
            "https://emissions.example.com",
            "--experiment-id",
            "exp-123",
            "--experiment-name",
            "cli-experiment",
            "--electricitymaps-api-token",
            "electricity-token",
            "--co2-signal-api-token",
            "legacy-token",
            "--tracking-mode",
            "process",
            "--on-csv-write",
            "update",
            "--logger-preamble",
            "monitor:",
            "--force-cpu-power",
            "75",
            "--force-ram-power",
            "20",
            "--pue",
            "1.25",
            "--wue",
            "0.4",
            "--force-carbon-intensity-g-co2e-kwh",
            "42.5",
            "--force-mode-cpu-load",
            "--no-allow-multiple-runs",
            "--rapl-include-dram",
            "--no-rapl-prefer-psys",
            "--",
            "python",
            "train.py",
        ],
    )

    assert result.exit_code == 0
    assert captured["args"] == ["python", "train.py"]
    assert captured["offline"] is True
    assert captured["kwargs"] == {
        "measure_power_secs": 10,
        "api_call_interval": 30,
        "log_level": "error",
        "project_name": "cli-project",
        "api_endpoint": "https://api.example.com",
        "api_key": "secret",
        "output_dir": "/tmp/emissions",
        "output_file": "custom.csv",
        "output_methods": "csv,logger",
        "save_to_file": False,
        "save_to_logger": True,
        "save_to_prometheus": True,
        "save_to_logfire": False,
        "prometheus_url": "http://localhost:9091",
        "gpu_ids": "0,2",
        "emissions_endpoint": "https://emissions.example.com",
        "experiment_id": "exp-123",
        "experiment_name": "cli-experiment",
        "electricitymaps_api_token": "electricity-token",
        "co2_signal_api_token": "legacy-token",
        "tracking_mode": "process",
        "on_csv_write": "update",
        "logger_preamble": "monitor:",
        "force_cpu_power": 75,
        "force_ram_power": 20,
        "pue": 1.25,
        "wue": 0.4,
        "force_carbon_intensity_g_co2e_kwh": 42.5,
        "force_mode_cpu_load": True,
        "allow_multiple_runs": False,
        "rapl_include_dram": True,
        "rapl_prefer_psys": False,
        "country_iso_code": "FRA",
        "region": None,
    }


def test_monitor_omits_unspecified_optional_tracker_options(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)

    ctx = SimpleNamespace(args=["python", "train.py"])
    cli_main.monitor(ctx=ctx, offline=True, country_iso_code="FRA")

    assert "pue" not in captured["kwargs"]
    assert "allow_multiple_runs" not in captured["kwargs"]
    assert "output_methods" not in captured["kwargs"]


def test_monitor_explicit_experiment_id_satisfies_online_validation(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: None)

    runner = CliRunner()
    result = runner.invoke(
        cli_main.codecarbon,
        [
            "monitor",
            "--experiment-id",
            "exp-from-cli",
            "--",
            "python",
            "train.py",
        ],
    )

    assert result.exit_code == 0
    assert captured["kwargs"]["experiment_id"] == "exp-from-cli"


def test_monitor_help_lists_explicit_tracker_options():
    runner = CliRunner()
    result = runner.invoke(
        cli_main.codecarbon, ["monitor", "--help"], terminal_width=200
    )

    assert result.exit_code == 0
    assert "--output-methods" in result.output
    assert "--pue" in result.output
    assert "--wue" in result.output
    assert "--force-cpu-power" in result.output
    assert "--rapl-include-dram" in result.output


def test_monitor_delegates_offline_flag_to_run_and_monitor(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["offline"] = offline
        captured["kwargs"] = kwargs
        return "ok"

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)

    ctx = SimpleNamespace(args=["python", "-c", "print(1)"])
    result = cli_main.monitor(
        ctx=ctx,
        offline=True,
        country_iso_code="FRA",
    )
    assert result == "ok"
    assert captured["offline"] is True
    assert captured["kwargs"]["country_iso_code"] == "FRA"


def test_monitor_delegates_online_mode_to_run_and_monitor(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["offline"] = offline
        captured["kwargs"] = kwargs
        return "ok"

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: "exp-1")

    ctx = SimpleNamespace(args=["python", "train.py"])
    result = cli_main.monitor(ctx=ctx, api=True)
    assert result == "ok"
    assert captured["offline"] is False
    assert captured["kwargs"]["save_to_api"] is True


def test_monitor_delegates_to_run_and_monitor_with_extra_args(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, **kwargs):
        captured["args"] = list(ctx.args)
        captured["kwargs"] = kwargs
        return "ok"

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: "exp-1")

    ctx = SimpleNamespace(args=["python", "train.py"])
    result = cli_main.monitor(ctx=ctx, api=False)
    assert result == "ok"
    assert captured["args"] == ["python", "train.py"]
    assert captured["kwargs"]["save_to_api"] is False


def test_monitor_no_api_skips_experiment_id_requirement(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["offline"] = offline
        captured["kwargs"] = kwargs
        return "ok"

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: None)

    ctx = SimpleNamespace(args=["python", "train.py"])
    result = cli_main.monitor(ctx=ctx, api=False)
    assert result == "ok"
    assert captured["offline"] is False
    assert captured["kwargs"]["save_to_api"] is False


def test_monitor_passes_log_level_to_run_and_monitor(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, offline=False, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr("codecarbon.cli.monitor.run_and_monitor", fake_run_and_monitor)

    ctx = SimpleNamespace(args=["echo", "hello"])
    cli_main.monitor(
        ctx=ctx,
        offline=True,
        country_iso_code="FRA",
        log_level="debug",
    )

    assert captured["kwargs"]["log_level"] == "debug"


def test_monitor_online_requires_experiment_id_for_wrapped_command(monkeypatch):
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: None)

    ctx = SimpleNamespace(args=["echo", "hi"])
    with pytest.raises(typer.Exit) as exc_info:
        cli_main.monitor(ctx=ctx, offline=False, api=True)
    assert exc_info.value.exit_code == 1
