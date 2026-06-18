import configparser
from unittest.mock import MagicMock, patch

import pytest

from codecarbon.core.api_client import clear_api_clients, get_or_create_api_client
from codecarbon.core.config import clear_config_cache, get_hierarchical_config


@pytest.fixture(autouse=True)
def reset_perf_caches():
    clear_config_cache()
    clear_api_clients()
    yield
    clear_config_cache()
    clear_api_clients()


def test_get_or_create_api_client_reuses_instance_and_resets_run_id():
    with patch("codecarbon.core.api_client.ApiClient._create_run") as mock_create_run:
        first = get_or_create_api_client(
            endpoint_url="http://test.com",
            experiment_id="exp-1",
            api_key="key",
            conf={"cpu_model": "CPU"},
        )
        first.run_id = "run-1"
        second = get_or_create_api_client(
            endpoint_url="http://test.com",
            experiment_id="exp-1",
            api_key="key",
            conf={"cpu_model": "CPU"},
        )

    assert first is second
    assert second.run_id is None
    mock_create_run.assert_not_called()


def test_get_hierarchical_config_uses_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".codecarbon.config"
    config_path.write_text("[codecarbon]\ncached=value\n", encoding="utf-8")
    read_count = {"value": 0}
    original_read = configparser.ConfigParser.read

    def counted_read(self, paths):
        read_count["value"] += 1
        return original_read(self, paths)

    with (
        patch("codecarbon.core.config.Path.home", return_value=tmp_path),
        patch(
            "codecarbon.core.config.parse_env_config", return_value={"codecarbon": {}}
        ),
        patch.object(configparser.ConfigParser, "read", counted_read),
    ):
        first = get_hierarchical_config()
        second = get_hierarchical_config()

    assert first == second == {"cached": "value"}
    assert read_count["value"] == 1


def test_logfire_configure_runs_once():
    from codecarbon.output_methods.metrics.logfire import (
        LogfireOutput,
        clear_logfire_cache,
    )

    clear_logfire_cache()
    with (
        patch("logfire.configure") as mock_configure,
        patch("logfire.metric_counter", return_value=MagicMock()),
        patch("logfire.metric_gauge", return_value=MagicMock()),
    ):
        LogfireOutput()
        LogfireOutput()

    assert mock_configure.call_count == 1
