"""Integration tests for telemetry tier resolution and config contract (Task 5)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import codecarbon.telemetry as telemetry_module
from codecarbon.core.config import get_config_file_settings
from codecarbon.core.telemetry_settings import resolve_telemetry_level
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.core.telemetry_settings import get_telemetry_api_url
from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker
from codecarbon.telemetry import (
    send_tier1_telemetry,
    send_tier2_public_emission,
    warn_if_telemetry_not_configured,
)
from tests.testutils import get_custom_mock_open

if sys.platform == "darwin":
    mock_platform_cli_setup = patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")


def _conf(level: str) -> str:
    return f"[codecarbon]\ntelemetry_level = {level}\n"


class TestTelemetryConfigContract(unittest.TestCase):
    def setUp(self) -> None:
        telemetry_module._TELEMETRY_CONFIGURE_WARNED = False

    def test_warns_once_when_telemetry_not_explicit(self):
        with patch("codecarbon.telemetry.logger.warning") as mock_warning:
            warn_if_telemetry_not_configured({}, TelemetryLevel.minimal)
            warn_if_telemetry_not_configured({}, TelemetryLevel.minimal)
        self.assertEqual(mock_warning.call_count, 1)
        self.assertIn("Tier 1", mock_warning.call_args[0][0])

    def test_no_warn_when_config_explicit(self):
        with patch("codecarbon.telemetry.logger.warning") as mock_warning:
            warn_if_telemetry_not_configured(
                {"telemetry_level": "disabled"}, TelemetryLevel.disabled
            )
        mock_warning.assert_not_called()

    def test_minimal_tier1_posts_once_per_session(self):
        telemetry_module._TIER1_SENT = False
        conf = {"python_version": "3.11", "os": "Linux", "codecarbon_version": "2.0"}
        with patch("codecarbon.telemetry.TelemetryClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_client_cls.return_value = mock_client
            self.assertTrue(send_tier1_telemetry(conf))
            self.assertFalse(send_tier1_telemetry(conf))
        mock_client_cls.assert_called_once()
        payload = mock_client_cls.call_args.kwargs["telemetry"]
        self.assertEqual(payload["telemetry_level"], TelemetryLevel.minimal.value)

    def test_tier1_posts_to_telemetry_endpoint(self):
        telemetry_module._TIER1_SENT = False
        with patch("codecarbon.core.telemetry_client.requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = "telemetry-id"
            send_tier1_telemetry(
                {"python_version": "3.11", "os": "Linux", "codecarbon_version": "2.0"},
                external_conf={"telemetry_api_url": "http://tier1.example"},
            )
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.kwargs["url"], "http://tier1.example/telemetry"
        )
        self.assertEqual(
            mock_post.call_args.kwargs["json"]["telemetry_level"],
            TelemetryLevel.minimal.value,
        )

    def test_legacy_env_codecarbon_telemetry_does_not_change_tier(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / ".codecarbon.config"
            local_path.write_text(_conf("minimal"))
            with patch(
                "codecarbon.core.config._config_file_paths",
                return_value=("/nonexistent/global", str(local_path)),
            ):
                with patch.dict(
                    os.environ,
                    {"CODECARBON_TELEMETRY": "disabled"},
                    clear=False,
                ):
                    from codecarbon.core.config import get_hierarchical_config

                    level = resolve_telemetry_level(
                        get_config_file_settings(),
                        external_conf=get_hierarchical_config(),
                    )
        self.assertEqual(level, TelemetryLevel.minimal)

    def test_env_codecarbon_telemetry_level_overrides_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / ".codecarbon.config"
            local_path.write_text(_conf("minimal"))
            with patch(
                "codecarbon.core.config._config_file_paths",
                return_value=("/nonexistent/global", str(local_path)),
            ):
                with patch.dict(
                    os.environ,
                    {"CODECARBON_TELEMETRY_LEVEL": "disabled"},
                    clear=False,
                ):
                    from codecarbon.core.config import get_hierarchical_config

                    level = resolve_telemetry_level(
                        get_config_file_settings(),
                        external_conf=get_hierarchical_config(),
                    )
        self.assertEqual(level, TelemetryLevel.disabled)

    def test_telemetry_api_url_env_used_for_tier2_client(self):
        with patch.dict(
            os.environ,
            {"CODECARBON_TELEMETRY_API_URL": "http://env-telemetry.example"},
            clear=False,
        ):
            url = get_telemetry_api_url({})
        self.assertEqual(url, "http://env-telemetry.example")

    def test_telemetry_api_url_from_config_overrides_default(self):
        url = get_telemetry_api_url(
            {"telemetry_api_url": "http://config-telemetry.example"}
        )
        self.assertEqual(url, "http://config-telemetry.example")


@mock_platform_cli_setup
class TestTrackerTelemetryFromConfig(unittest.TestCase):
    def setUp(self) -> None:
        telemetry_module._TIER1_SENT = False
        telemetry_module._TIER2_SENT = False
        telemetry_module._TELEMETRY_CONFIGURE_WARNED = False
        self._config_patcher = None

    def tearDown(self) -> None:
        if self._config_patcher:
            self._config_patcher.stop()

    def _mock_config(self, conf: str) -> None:
        self._config_patcher = patch(
            "builtins.open", new_callable=get_custom_mock_open(conf, conf)
        )
        self._config_patcher.start()

    def test_disabled_no_tier1_post_or_tier2_emission(self, mock_cli_setup):
        self._mock_config(_conf("disabled"))
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            with patch("codecarbon.telemetry.ApiClient") as mock_api_cls:
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    tracker = EmissionsTracker(
                        measure_power_secs=1,
                        save_to_api=False,
                        save_to_file=False,
                    )
                    tracker.start()
                    tracker.stop()
        mock_telemetry_cls.assert_not_called()
        mock_api_cls.assert_not_called()

    def test_minimal_posts_tier1_on_init_not_tier2_on_stop(self, mock_cli_setup):
        self._mock_config(_conf("minimal"))
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_telemetry_cls.return_value = mock_client
            with patch("codecarbon.telemetry.ApiClient") as mock_api_cls:
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    tracker = EmissionsTracker(
                        measure_power_secs=1,
                        save_to_api=False,
                        save_to_file=False,
                    )
                    tracker.start()
                    tracker.stop()
        mock_telemetry_cls.assert_called_once()
        mock_client.add_telemetry.assert_called_once()
        mock_api_cls.assert_not_called()

    def test_extensive_posts_tier1_and_tier2_on_stop(self, mock_cli_setup):
        self._mock_config(_conf("extensive"))
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_telemetry_cls.return_value = mock_client
            with patch("codecarbon.telemetry.ApiClient") as mock_api_cls:
                mock_api = MagicMock()
                mock_api.add_emission.return_value = True
                mock_api_cls.return_value = mock_api
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    tracker = EmissionsTracker(
                        measure_power_secs=1,
                        save_to_api=False,
                        save_to_file=False,
                    )
                    tracker.start()
                    tracker.stop()
        mock_telemetry_cls.assert_called_once()
        mock_client.add_telemetry.assert_called_once()
        mock_api.add_emission.assert_called_once()

    def test_offline_minimal_with_save_to_api_false_still_posts_tier1(
        self, mock_cli_setup
    ):
        self._mock_config(_conf("minimal"))
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_telemetry_cls.return_value = mock_client
            OfflineEmissionsTracker(
                country_iso_code="CAN",
                save_to_api=False,
                save_to_file=False,
            )
        mock_telemetry_cls.assert_called_once()

    def test_warns_when_config_has_no_explicit_telemetry_level(self, mock_cli_setup):
        self._mock_config("[codecarbon]\n")
        env_without_telemetry = {
            key: value
            for key, value in os.environ.items()
            if key.lower()
            not in (
                "codecarbon_telemetry",
                "codecarbon_telemetry_level",
            )
        }
        with patch.dict(os.environ, env_without_telemetry, clear=True):
            with patch("codecarbon.telemetry.logger.warning") as mock_warning:
                with patch(
                    "codecarbon.telemetry.TelemetryClient"
                ) as mock_telemetry_cls:
                    mock_client = MagicMock()
                    mock_client.add_telemetry.return_value = "telemetry-id"
                    mock_telemetry_cls.return_value = mock_client
                    with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                        EmissionsTracker(save_to_api=False, save_to_file=False)
        configure_warnings = [
            c
            for c in mock_warning.call_args_list
            if c[0] and "telemetry" in str(c[0][0]).lower()
        ]
        self.assertEqual(len(configure_warnings), 1)

    def test_no_configure_warn_when_telemetry_level_kwarg_set(self, mock_cli_setup):
        self._mock_config("[codecarbon]\n")
        with patch("codecarbon.telemetry.logger.warning") as mock_warning:
            with patch("codecarbon.telemetry.TelemetryClient"):
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    EmissionsTracker(
                        telemetry_level="disabled",
                        save_to_api=False,
                        save_to_file=False,
                    )
        configure_warnings = [
            c for c in mock_warning.call_args_list if c[0] and "Tier 1" in str(c[0][0])
        ]
        self.assertEqual(len(configure_warnings), 0)

    def test_env_telemetry_disabled_still_minimal_tier1_when_config_minimal(
        self, mock_cli_setup
    ):
        self._mock_config(_conf("minimal"))
        with patch.dict(os.environ, {"CODECARBON_TELEMETRY": "disabled"}, clear=False):
            with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
                mock_client = MagicMock()
                mock_client.add_telemetry.return_value = "telemetry-id"
                mock_telemetry_cls.return_value = mock_client
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    EmissionsTracker(save_to_api=False, save_to_file=False)
        mock_telemetry_cls.assert_called_once()


class TestTier2ApiSettings(unittest.TestCase):
    def test_tier2_uses_resolved_api_url(self):
        telemetry_module._TIER2_SENT = False
        from codecarbon.output_methods.emissions_data import EmissionsData

        emissions = EmissionsData(
            timestamp="2020-01-01T00:00:00",
            project_name="test",
            run_id="run-1",
            experiment_id="exp-1",
            duration=1.0,
            emissions=0.001,
            emissions_rate=0.001,
            cpu_power=0.0,
            gpu_power=0.0,
            ram_power=0.0,
            cpu_energy=0.0,
            gpu_energy=0.0,
            ram_energy=0.0,
            energy_consumed=0.01,
            water_consumed=0.0,
            country_name="",
            country_iso_code="",
            region="",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.11",
            codecarbon_version="2.0",
            cpu_count=1.0,
            cpu_model="",
            gpu_count=0.0,
            gpu_model="",
            longitude=0.0,
            latitude=0.0,
            ram_total_size=8.0,
            tracking_mode="machine",
        )
        external_conf = {"telemetry_api_url": "http://custom.example"}
        with patch("codecarbon.telemetry.ApiClient") as mock_api_cls:
            mock_api = MagicMock()
            mock_api.add_emission.return_value = True
            mock_api_cls.return_value = mock_api
            send_tier2_public_emission({}, emissions, external_conf=external_conf)
        mock_api_cls.assert_called_once()
        self.assertEqual(
            mock_api_cls.call_args.kwargs["endpoint_url"], "http://custom.example"
        )


if __name__ == "__main__":
    unittest.main()
