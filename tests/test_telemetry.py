import sys
import tempfile
import unittest
from unittest.mock import ANY, MagicMock, patch

from codecarbon.core.telemetry import Telemetry
from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker
from codecarbon.output_methods.emissions_data import EmissionsData
from tests.testutils import ensure_telemetry_run_duration, get_custom_mock_open

if sys.platform == "darwin":
    mock_platform_cli_setup = patch(
        "codecarbon.core.powermetrics.ApplePowermetrics._setup_cli"
    )
else:
    mock_platform_cli_setup = patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")

disabled_conf = "[codecarbon]\ntelemetry_level = disabled\n"
minimal_conf = "[codecarbon]\ntelemetry_level = minimal\n"
extensive_conf = "[codecarbon]\ntelemetry_level = extensive\n"


class TestTelemetryTiersAtStop(unittest.TestCase):
    def _emissions(self) -> EmissionsData:
        return EmissionsData(
            timestamp="2020-01-01T00:00:00",
            project_name="test",
            run_id="run-1",
            experiment_id="exp-1",
            duration=10.0,
            emissions=0.001,
            emissions_rate=0.0001,
            cpu_power=0.0,
            gpu_power=0.0,
            ram_power=0.0,
            cpu_energy=0.0,
            gpu_energy=0.0,
            ram_energy=0.0,
            energy_consumed=0.01,
            water_consumed=0.0,
            country_name="France",
            country_iso_code="FRA",
            region="idf",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.11",
            codecarbon_version="2.0",
            cpu_count=1.0,
            cpu_model="cpu",
            gpu_count=0.0,
            gpu_model="",
            longitude=0.0,
            latitude=0.0,
            ram_total_size=8.0,
            tracking_mode="machine",
        )

    def test_tier1_posts_private_telemetry(self):
        tracker = MagicMock()
        tracker._config_file_conf = {}
        tracker._external_conf = {}
        tracker._telemetry_override = None
        tracker._conf = {"os": "Linux", "tracking_mode": "machine"}
        tracker._hardware = []
        tracker._resource_tracker = None
        tracker._save_to_api = False
        tracker._save_to_file = False
        tracker._save_to_logger = False
        tracker._emissions_endpoint = None
        tracker._save_to_prometheus = False
        tracker._save_to_logfire = False
        tracker._tasks = {}
        tracker._measure_power_secs = 15
        emissions = self._emissions()
        telemetry = Telemetry.from_tracker(tracker)
        with patch(
            "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
        ) as mock_post:
            telemetry.send_at_stop(tracker, emissions)
        mock_post.assert_called_once()
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertNotIn("total_emissions_kg", payload)

    def test_tier1_skips_short_duration_at_dispatcher(self):
        tracker = MagicMock()
        tracker._config_file_conf = {}
        tracker._external_conf = {}
        tracker._telemetry_override = None
        emissions = self._emissions()
        emissions.duration = 0.5
        telemetry = Telemetry.from_tracker(tracker)
        with patch("codecarbon.core.telemetry.dispatcher.post_private") as mock_post:
            telemetry.send_at_stop(tracker, emissions)
        mock_post.assert_not_called()

    def test_tier2_uses_api_client(self):
        tracker = MagicMock()
        tracker._conf = {"os": "Linux"}
        tracker._config_file_conf = {"telemetry_level": "extensive"}
        tracker._external_conf = {}
        tracker._telemetry_override = None
        emissions = self._emissions()
        telemetry = Telemetry.from_tracker(tracker)
        with patch(
            "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
        ):
            with patch("codecarbon.core.telemetry.client.ApiClient") as mock_api_cls:
                mock_api = MagicMock()
                mock_api.add_emission.return_value = True
                mock_api_cls.return_value = mock_api
                telemetry.send_at_stop(tracker, emissions)
        mock_api_cls.assert_called_once()
        mock_api.add_emission.assert_called_once()
        mock_api_cls.assert_called_with(
            endpoint_url=ANY,
            experiment_id=ANY,
            api_key=ANY,
            conf=tracker._conf,
            create_run_automatically=True,
        )


@mock_platform_cli_setup
class TestTrackerTelemetry(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = None
        Telemetry._default_warning_shown = False

    def tearDown(self) -> None:
        if self.patcher:
            self.patcher.stop()
        self.temp_dir.cleanup()
        Telemetry._default_warning_shown = False

    def _start_config_mock(self, conf: str) -> None:
        self.patcher = patch(
            "builtins.open", new_callable=get_custom_mock_open(conf, conf)
        )
        self.patcher.start()

    def test_emissions_tracker_does_not_send_telemetry_on_init(self, mock_cli_setup):
        self._start_config_mock(minimal_conf)
        with patch("codecarbon.core.telemetry.dispatcher.post_private") as mock_post:
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                EmissionsTracker(save_to_api=False, save_to_file=False)
        mock_post.assert_not_called()

    def test_emissions_tracker_sends_telemetry_on_stop_when_minimal(
        self, mock_cli_setup
    ):
        self._start_config_mock(minimal_conf)
        with ensure_telemetry_run_duration():
            with patch(
                "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
            ) as mock_post:
                with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                    tracker = EmissionsTracker(
                        measure_power_secs=1,
                        save_to_api=False,
                        save_to_file=False,
                    )
                    tracker.start()
                    tracker.stop()
        mock_post.assert_called_once()
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["telemetry_level"], "minimal")
        self.assertNotIn("total_emissions_kg", payload)

    def test_emissions_tracker_skips_telemetry_when_disabled(self, mock_cli_setup):
        self._start_config_mock(disabled_conf)
        with patch("codecarbon.core.telemetry.dispatcher.post_private") as mock_post:
            with patch("codecarbon.external.geography.GeoMetadata.from_geo_js"):
                tracker = EmissionsTracker(
                    measure_power_secs=1,
                    save_to_api=False,
                    save_to_file=False,
                )
                tracker.start()
                tracker.stop()
        mock_post.assert_not_called()

    def test_tier2_sends_tier1_and_api_client_on_stop(self, mock_cli_setup):
        self._start_config_mock(extensive_conf)
        with ensure_telemetry_run_duration():
            with patch(
                "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
            ) as mock_post:
                with patch(
                    "codecarbon.core.telemetry.client.ApiClient"
                ) as mock_api_cls:
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
        mock_post.assert_called_once()
        mock_api_cls.assert_called_once()
        mock_api.add_emission.assert_called_once()

    def test_offline_tracker_sends_on_stop(self, mock_cli_setup):
        self._start_config_mock(minimal_conf)
        with ensure_telemetry_run_duration():
            with patch(
                "codecarbon.core.telemetry.dispatcher.post_private", return_value=True
            ) as mock_post:
                tracker = OfflineEmissionsTracker(
                    country_iso_code="CAN",
                    save_to_api=False,
                    save_to_file=False,
                )
                tracker.start()
                tracker.stop()
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
