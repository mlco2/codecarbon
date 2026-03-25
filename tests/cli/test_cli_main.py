"""Tests for the CodeCarbon CLI main function."""

from types import SimpleNamespace

import pytest
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
    monkeypatch.setattr(cli_main, "ApiClient", FakeApiClient)
    monkeypatch.setattr(cli_main, "get_access_token", fake_get_access_token)

    result = runner.invoke(cli_main.codecarbon, ["test-api"])
    assert result.exit_code == 0
    assert "fake-org" in result.output


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

    monkeypatch.setattr(cli_main, "EmissionsTracker", FakeTracker)
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

    monkeypatch.setattr(cli_main, "ApiClient", FakeApiClient)
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
    monkeypatch.setattr(cli_main, "get_access_token", fake_get_access_token)

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
    calls = {"authorize": 0, "set_token": None, "check_auth": 0}

    class FakeApiClient:
        def __init__(self, endpoint_url=None):
            self.endpoint_url = endpoint_url

        def set_access_token(self, token):
            calls["set_token"] = token

        def check_auth(self):
            calls["check_auth"] += 1

    monkeypatch.setattr(cli_main, "ApiClient", FakeApiClient)
    monkeypatch.setattr(
        cli_main,
        "authorize",
        lambda: calls.__setitem__("authorize", calls["authorize"] + 1),
    )
    monkeypatch.setattr(cli_main, "get_access_token", lambda: "login-token")

    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["login"])
    assert result.exit_code == 0
    assert calls["authorize"] == 1
    assert calls["set_token"] == "login-token"
    assert calls["check_auth"] == 1


def test_get_api_key_uses_bearer_token(monkeypatch):
    captured = {}

    class FakeResponse:
        def json(self):
            return {"token": "project-api-token"}

    def fake_post(url, json, headers):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(cli_main, "get_access_token", lambda: "access-token")
    monkeypatch.setattr(cli_main.requests, "post", fake_post)

    token = cli_main.get_api_key("proj-123")
    assert token == "project-api-token"
    assert captured["url"].endswith("/projects/proj-123/api-tokens")
    assert captured["json"]["project_id"] == "proj-123"
    assert captured["headers"]["Authorization"] == "Bearer access-token"


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

    monkeypatch.setattr(cli_main, "ApiClient", FakeApiClient)
    monkeypatch.setattr(cli_main, "get_access_token", lambda: "fake-token")
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

    monkeypatch.setattr(cli_main, "OfflineEmissionsTracker", FakeOfflineTracker)
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


def test_monitor_delegates_to_run_and_monitor_with_extra_args(monkeypatch):
    captured = {}

    def fake_run_and_monitor(ctx, **kwargs):
        captured["args"] = list(ctx.args)
        captured["kwargs"] = kwargs
        return "ok"

    monkeypatch.setattr(cli_main, "run_and_monitor", fake_run_and_monitor)
    monkeypatch.setattr(cli_main, "get_existing_exp_id", lambda: "exp-1")

    ctx = SimpleNamespace(args=["python", "train.py"])
    result = cli_main.monitor(ctx=ctx, api=False)
    assert result == "ok"
    assert captured["args"] == ["python", "train.py"]
    assert captured["kwargs"]["save_to_api"] is False
