"""Tests for the CodeCarbon CLI main function."""

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
    monkeypatch.setattr(cli_main, "_get_access_token", fake_get_access_token)

    result = runner.invoke(cli_main.codecarbon, ["test-api"])
    assert result.exit_code == 0
    assert "fake-org" in result.output


def test_monitor_offline_requires_country_iso_code():
    runner = CliRunner()
    result = runner.invoke(cli_main.codecarbon, ["monitor", "--offline"])
    assert result.exit_code != 0
    assert "country_iso_code is required for offline mode" in result.output


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
