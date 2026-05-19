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
    collect_tier1_payload,
    send_tier1_telemetry,
)
from tests.testutils import get_custom_mock_open

if sys.platform == "darwin":
    mock_platform_cli_setup = patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = patch(
        "codecarbon.core.cpu.IntelPowerGadget._setup_cli"
    )

empty_conf = "[codecarbon]"


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

    def test_collect_tier1_payload_delegates_to_builder(self):
        self.assertIs(collect_tier1_payload, build_minimal_telemetry_dict)


class TestTier1Send(unittest.TestCase):
    def test_send_tier1_telemetry_sends_once_per_session(self):
        telemetry_module._TIER1_SENT = False
        conf = {
            "python_version": "3.11.0",
            "os": "Linux",
            "cpu_count": 4,
            "cpu_model": "Intel i5",
            "gpu_count": 0,
            "codecarbon_version": "2.0.0",
        }
        with patch(
            "codecarbon.core.telemetry_client.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201, json=lambda: "telemetry-id"
            )
            result = send_tier1_telemetry(conf, endpoint_url="http://test.com")
            self.assertTrue(result)
            self.assertEqual(mock_post.call_count, 1)
            body = mock_post.call_args.kwargs["json"]
            self.assertEqual(body["telemetry_level"], "minimal")
            result = send_tier1_telemetry(conf, endpoint_url="http://test.com")
            self.assertFalse(result)
            self.assertEqual(mock_post.call_count, 1)

    def test_send_tier1_telemetry_fails_silently(self):
        telemetry_module._TIER1_SENT = False
        conf = {
            "python_version": "3.11.0",
            "os": "Linux",
            "cpu_count": 4,
            "codecarbon_version": "2.0.0",
        }
        with patch(
            "codecarbon.core.telemetry_client.requests.post",
            side_effect=Exception("network error"),
        ):
            with patch("codecarbon.core.telemetry_client.logger.error") as mock_logger:
                result = send_tier1_telemetry(conf, endpoint_url="http://test.com")
                self.assertFalse(result)
                mock_logger.assert_called()


@mock_platform_cli_setup
class TestTrackerTelemetry(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.patcher = patch(
            "builtins.open", new_callable=get_custom_mock_open(empty_conf, empty_conf)
        )
        self.mock_open = self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_emissions_tracker_sends_tier1_telemetry_by_default(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        with patch(
            "codecarbon.core.telemetry_client.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201, json=lambda: "telemetry-id"
            )
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                EmissionsTracker(
                    send_telemetry=True, save_to_api=False, save_to_file=False
                )
        self.assertTrue(mock_post.called)

    def test_emissions_tracker_skips_tier1_when_opted_out(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        with patch("codecarbon.core.telemetry_client.requests.post") as mock_post:
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                EmissionsTracker(
                    send_telemetry=False, save_to_api=False, save_to_file=False
                )
        self.assertFalse(mock_post.called)

    def test_offline_tracker_sends_tier1_telemetry_by_default(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        with patch(
            "codecarbon.core.telemetry_client.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201, json=lambda: "telemetry-id"
            )
            OfflineEmissionsTracker(
                country_iso_code="CAN",
                send_telemetry=True,
                save_to_api=False,
                save_to_file=False,
            )
        self.assertTrue(mock_post.called)

    def test_offline_tracker_skips_tier1_when_opted_out(self, mock_cli_setup):
        telemetry_module._TIER1_SENT = False
        with patch("codecarbon.core.telemetry_client.requests.post") as mock_post:
            OfflineEmissionsTracker(
                country_iso_code="CAN",
                send_telemetry=False,
                save_to_api=False,
                save_to_file=False,
            )
        self.assertFalse(mock_post.called)


if __name__ == "__main__":
    unittest.main()
