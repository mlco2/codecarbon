import platform
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import codecarbon.telemetry as telemetry_module
from codecarbon.core.telemetry_schemas import TelemetryLevel
from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker
from codecarbon.telemetry import (
    build_minimal_telemetry_dict,
    send_tier1_telemetry,
    send_tier2_public_emission,
)
from tests.testutils import get_custom_mock_open

if sys.platform == "darwin":
    mock_platform_cli_setup = patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")

disabled_conf = "[codecarbon]\ntelemetry_level = disabled\n"
minimal_conf = "[codecarbon]\ntelemetry_level = minimal\n"
extensive_conf = "[codecarbon]\ntelemetry_level = extensive\n"


class TestTelemetry(unittest.TestCase):
    def test_build_minimal_telemetry_dict_maps_tracker_conf(self):
        conf = {
            "python_version": platform.python_version(),
            "os": platform.platform(),
            "cpu_count": 8,
            "cpu_physical_count": 4,
            "cpu_model": "Intel Core i7",
            "gpu_count": 1,
            "gpu_model": "NVIDIA RTX 3080",
            "ram_total_size": 32.0,
            "codecarbon_version": "2.0.0",
            "tracking_mode": "machine",
            "country_iso_code": "FRA",
            "provider": "aws",
            "region": "eu-west-1",
        }
        payload = build_minimal_telemetry_dict(conf)
        self.assertEqual(payload["telemetry_level"], TelemetryLevel.minimal.value)
        self.assertIn("timestamp", payload)
        self.assertEqual(payload["python_version"], conf["python_version"])
        self.assertEqual(payload["ram_total_size_gb"], conf["ram_total_size"])
        self.assertEqual(payload["cloud_provider"], conf["provider"])
        self.assertEqual(payload["cloud_region"], conf["region"])


class TestTier1Send(unittest.TestCase):
    def test_send_tier1_telemetry_posts_once_per_session(self):
        telemetry_module._TIER1_SENT = False
        conf = {
            "python_version": "3.11.0",
            "os": "Linux",
            "cpu_count": 4,
            "cpu_model": "Intel i5",
            "gpu_count": 0,
            "codecarbon_version": "2.0.0",
        }
        with patch("codecarbon.telemetry.TelemetryClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_client_cls.return_value = mock_client
            result = send_tier1_telemetry(conf)
            self.assertTrue(result)
            result = send_tier1_telemetry(conf)
            self.assertFalse(result)
        mock_client_cls.assert_called_once()
        mock_client.add_telemetry.assert_called_once()
        call_kwargs = mock_client_cls.call_args.kwargs
        self.assertEqual(
            call_kwargs["telemetry"]["telemetry_level"], TelemetryLevel.minimal.value
        )

    def test_send_tier1_telemetry_uses_resolved_api_url_and_key(self):
        telemetry_module._TIER1_SENT = False
        external_conf = {
            "telemetry_api_url": "http://custom-tier1.example",
            "telemetry_api_key": "cpt_custom",
        }
        with patch("codecarbon.telemetry.TelemetryClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_client_cls.return_value = mock_client
            send_tier1_telemetry(
                {"codecarbon_version": "2.0"}, external_conf=external_conf
            )
        self.assertEqual(
            mock_client_cls.call_args.kwargs["endpoint_url"],
            "http://custom-tier1.example",
        )
        self.assertEqual(mock_client_cls.call_args.kwargs["api_key"], "cpt_custom")

    def test_send_tier1_telemetry_fails_silently(self):
        telemetry_module._TIER1_SENT = False
        with patch(
            "codecarbon.telemetry.build_minimal_telemetry_dict",
            side_effect=RuntimeError("build failed"),
        ):
            with patch("codecarbon.telemetry.logger.error") as mock_logger:
                result = send_tier1_telemetry({})
                self.assertFalse(result)
                mock_logger.assert_called()


class TestTier2Send(unittest.TestCase):
    def test_send_tier2_public_emission_sends_once_per_session(self):
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
        with patch("codecarbon.telemetry.ApiClient") as mock_api_cls:
            mock_api = MagicMock()
            mock_api.add_emission.return_value = True
            mock_api_cls.return_value = mock_api
            result = send_tier2_public_emission({}, emissions)
            self.assertTrue(result)
            mock_api.add_emission.assert_called_once()
            result = send_tier2_public_emission({}, emissions)
            self.assertFalse(result)
            mock_api.add_emission.assert_called_once()


@mock_platform_cli_setup
class TestTrackerTelemetry(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.patcher = None

    def tearDown(self) -> None:
        if self.patcher:
            self.patcher.stop()
        self.temp_dir.cleanup()

    def _start_config_mock(self, conf: str) -> None:
        self.patcher = patch(
            "builtins.open", new_callable=get_custom_mock_open(conf, conf)
        )
        self.patcher.start()

    def test_emissions_tracker_sends_tier1_when_minimal_config(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        self._start_config_mock(minimal_conf)
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            mock_client = MagicMock()
            mock_client.add_telemetry.return_value = "telemetry-id"
            mock_telemetry_cls.return_value = mock_client
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                EmissionsTracker(save_to_api=False, save_to_file=False)
        mock_telemetry_cls.assert_called_once()
        mock_client.add_telemetry.assert_called_once()

    def test_emissions_tracker_skips_tier1_when_disabled_config(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        self._start_config_mock(disabled_conf)
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                EmissionsTracker(save_to_api=False, save_to_file=False)
        mock_telemetry_cls.assert_not_called()

    def test_offline_tracker_sends_tier1_when_minimal_config(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        self._start_config_mock(minimal_conf)
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

    def test_offline_tracker_skips_tier1_when_disabled_config(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        self._start_config_mock(disabled_conf)
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            OfflineEmissionsTracker(
                country_iso_code="CAN",
                save_to_api=False,
                save_to_file=False,
            )
        mock_telemetry_cls.assert_not_called()

    def test_extensive_sends_tier1_on_init_and_tier2_on_stop(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        telemetry_module._TIER2_SENT = False
        self._start_config_mock(extensive_conf)
        with patch("codecarbon.telemetry.TelemetryClient") as mock_telemetry_cls:
            mock_telemetry = MagicMock()
            mock_telemetry.add_telemetry.return_value = "telemetry-id"
            mock_telemetry_cls.return_value = mock_telemetry
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
        mock_telemetry.add_telemetry.assert_called_once()
        mock_api.add_emission.assert_called_once()


if __name__ == "__main__":
    unittest.main()
