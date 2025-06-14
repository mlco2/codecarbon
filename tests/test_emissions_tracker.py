import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd
import requests
import responses

from codecarbon.core.units import Energy, Power
from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)
from codecarbon.external.geography import CloudMetadata
from tests.fake_modules import pynvml as fake_pynvml
from tests.testdata import (
    GEO_METADATA_CANADA,
    TWO_GPU_DETAILS_RESPONSE,
    TWO_GPU_DETAILS_RESPONSE_HANDLES,
)
from tests.testutils import get_custom_mock_open, get_test_data_source


def heavy_computation(run_time_secs: float = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        pass


empty_conf = "[codecarbon]"


@mock.patch("codecarbon.core.gpu.pynvml", fake_pynvml)
@mock.patch("codecarbon.core.gpu.is_gpu_details_available", return_value=True)
@mock.patch(
    "codecarbon.external.hardware.AllGPUDevices.get_gpu_details",
    return_value=TWO_GPU_DETAILS_RESPONSE,
)
@mock.patch(
    "codecarbon.emissions_tracker.EmissionsTracker._get_cloud_metadata",
    return_value=CloudMetadata(provider=None, region=None),
)
@mock.patch("codecarbon.core.cpu.IntelPowerGadget._log_values")
@mock.patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")
class TestCarbonTracker(unittest.TestCase):
    def setUp(self) -> None:
        fake_pynvml.DETAILS = TWO_GPU_DETAILS_RESPONSE_HANDLES
        self.data_source = get_test_data_source()
        self.project_name = "project_foo"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.emissions_file_path = self.temp_path / "emissions.csv"
        # builtins.open is patched not to open ~/.codecarbon.config nor
        # ./.codecarbon.config so that the user's local configuration does not
        # alter tests
        patcher = mock.patch(
            "builtins.open", new_callable=get_custom_mock_open(empty_conf, empty_conf)
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def tearDown(self) -> None:
        fake_pynvml.INIT_MOCK.reset_mock()
        self.temp_dir.cleanup()

    @responses.activate
    def test_carbon_tracker_TWO_GPU_PRIVATE_INFRA_CANADA(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN
        responses.add(
            responses.GET,
            "https://get.geojs.io/v1/ip/geo.json",
            json=GEO_METADATA_CANADA,
            status=200,
        )
        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)
        # WHEN
        tracker.start()
        heavy_computation()
        emissions = tracker.stop()

        # THEN
        self.assertGreaterEqual(
            mocked_get_gpu_details.call_count, 2
        )  # at least 2 times in 5 seconds + once for init >= 3
        self.assertEqual(3, mocked_is_gpu_details_available.call_count)
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
            "https://get.geojs.io/v1/ip/geo.json", responses.calls[0].request.url
        )
        self.assertIsInstance(emissions, float)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)

    @mock.patch("codecarbon.external.geography.requests.get")
    def test_carbon_tracker_timeout(
        self,
        mocked_requests_get,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN

        # breakpoint()

        def raise_timeout_exception(*args, **kwargs):
            raise requests.exceptions.Timeout()

        mocked_requests_get.side_effect = raise_timeout_exception

        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        # WHEN
        tracker.start()
        heavy_computation(run_time_secs=2)
        emissions = tracker.stop()
        self.assertEqual(2, mocked_requests_get.call_count)
        self.assertIsInstance(emissions, float)
        self.assertAlmostEqual(1.1037980397280433e-05, emissions, places=2)

    def test_graceful_start_failure(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        def raise_exception(*args, **kwargs):
            raise Exception()

        mocked_scheduler = mock.MagicMock()
        mocked_scheduler.start = raise_exception
        tracker._scheduler = mocked_scheduler
        tracker.start()

    def test_graceful_stop_failure(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        def raise_exception(*args, **kwargs):
            raise Exception()

        tracker.start()
        heavy_computation(1)
        tracker._measure_power = raise_exception
        tracker.stop()

    @responses.activate
    def test_decorator_ONLINE_NO_ARGS(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN
        responses.add(
            responses.GET,
            "https://get.geojs.io/v1/ip/geo.json",
            json=GEO_METADATA_CANADA,
            status=200,
        )

        # WHEN
        @track_emissions(project_name=self.project_name, output_dir=self.temp_path)
        def dummy_train_model():
            return 42

        dummy_train_model()

        # THEN
        self.verify_output_file(self.emissions_file_path, 2)

    @responses.activate
    def test_decorator_ONLINE_WITH_ARGS(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN
        responses.add(
            responses.GET,
            "https://get.geojs.io/v1/ip/geo.json",
            json=GEO_METADATA_CANADA,
            status=200,
        )

        # WHEN
        @track_emissions(project_name=self.project_name, output_dir=self.temp_path)
        def dummy_train_model():
            return 42

        dummy_train_model()

        # THEN
        self.verify_output_file(self.emissions_file_path, 2)

    def test_decorator_OFFLINE_NO_COUNTRY(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # WHEN

        @track_emissions(offline=True)
        def dummy_train_model():
            return 42

        self.assertRaises(Exception, dummy_train_model)

    def test_decorator_OFFLINE_WITH_LOC_ARGS(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN

        @track_emissions(
            offline=True,
            country_iso_code="CAN",
            project_name=self.project_name,
            output_dir=self.temp_path,
            experiment_id="test",
        )
        def dummy_train_model():
            return 42

        dummy_train_model()
        self.verify_output_file(self.emissions_file_path, 2)

    def test_decorator_OFFLINE_WITH_CLOUD_ARGS(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN

        @track_emissions(
            offline=True,
            cloud_provider="gcp",
            cloud_region="us-central1",
            output_dir=self.temp_path,
            experiment_id="test",
        )
        def dummy_train_model():
            return 42

        dummy_train_model()
        self.verify_output_file(self.emissions_file_path, 2)

    def test_offline_tracker_country_name(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            experiment_id="test",
        )
        tracker.start()
        heavy_computation(run_time_secs=2)
        tracker.stop()

        emissions_df = pd.read_csv(self.emissions_file_path)

        self.assertEqual("United States", emissions_df["country_name"].values[0])
        self.assertEqual("USA", emissions_df["country_iso_code"].values[0])

    def test_offline_tracker_invalid_headers(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            experiment_id="test",
        )
        emissions = os.path.join(
            os.path.dirname(__file__), "test_data", "emissions_invalid_headers.csv"
        )
        shutil.copyfile(emissions, self.emissions_file_path)
        tracker.start()
        heavy_computation(run_time_secs=2)
        tracker.stop()

        emissions_df = pd.read_csv(self.emissions_file_path)
        emissions_backup_df = pd.read_csv(
            self.emissions_file_path.with_suffix(".csv.bak")
        )

        self.verify_output_file(self.emissions_file_path, 2)
        self.verify_output_file(self.emissions_file_path.with_suffix(".csv.bak"), 2)

        self.assertEqual("United States", emissions_df["country_name"].values[0])
        self.assertEqual("Morocco", emissions_backup_df["country_name"].values[0])

    def test_offline_tracker_valid_headers(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            experiment_id="test",
        )
        emissions = os.path.join(
            os.path.dirname(__file__), "test_data", "emissions_valid_headers.csv"
        )
        shutil.copyfile(emissions, self.emissions_file_path)
        tracker.start()
        heavy_computation(run_time_secs=2)
        tracker.stop()

        emissions_df = pd.read_csv(self.emissions_file_path)

        self.verify_output_file(self.emissions_file_path, 3)

        print(emissions_df["cpu_power"].values[0])

        self.assertAlmostEqual(0.269999999999999, emissions_df["cpu_power"].values[0])
        self.assertEqual("Morocco", emissions_df["country_name"].values[0])
        self.assertEqual("United States", emissions_df["country_name"].values[1])

    def verify_output_file(self, file_path: str, num_lines: int) -> None:
        with open(file_path, "r") as f:
            lines = [line.rstrip() for line in f]
        assert len(lines) == num_lines

    @responses.activate
    def test_carbon_tracker_online_context_manager_TWO_GPU_PRIVATE_INFRA_CANADA(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        # GIVEN
        responses.add(
            responses.GET,
            "https://get.geojs.io/v1/ip/geo.json",
            json=GEO_METADATA_CANADA,
            status=200,
        )

        # WHEN
        with EmissionsTracker(measure_power_secs=1, save_to_file=False) as tracker:
            heavy_computation()

        # THEN
        self.assertGreaterEqual(
            mocked_get_gpu_details.call_count, 2
        )  # at least 2 times in 5 seconds + once for init >= 3
        self.assertEqual(3, mocked_is_gpu_details_available.call_count)
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
            "https://get.geojs.io/v1/ip/geo.json", responses.calls[0].request.url
        )
        self.assertIsInstance(tracker.final_emissions, float)
        self.assertAlmostEqual(tracker.final_emissions, 6.262572537957655e-05, places=2)

    @mock.patch(
        "codecarbon.external.ram.RAM.measure_power_and_energy"
    )  # Corrected path for RAM
    @mock.patch(
        "codecarbon.external.hardware.CPU.measure_power_and_energy"
    )  # Path for CPU is likely correct
    def test_task_energy_with_live_update_interference(
        self,
        mock_cpu_measure,  # Method decorator (innermost)
        mock_ram_measure,  # Method decorator (outermost)
        mock_setup_intel_cli,  # Class decorator (innermost)
        mock_log_values,  # Class decorator
        mocked_env_cloud_details,  # Class decorator
        mocked_get_gpu_details,  # Class decorator
        mocked_is_gpu_details_available,  # Class decorator (outermost relevant one)
    ):
        # --- Test Setup ---
        # Configure mocks to return specific, non-zero energy values
        cpu_energy_val_task = 0.0001
        ram_energy_val_task = 0.00005
        mock_cpu_measure.return_value = (
            Power.from_watts(10),
            Energy.from_energy(kWh=cpu_energy_val_task),
        )
        mock_ram_measure.return_value = (
            Power.from_watts(5),
            Energy.from_energy(kWh=ram_energy_val_task),
        )

        tracker = EmissionsTracker(
            project_name="TestLiveUpdateInterference",
            measure_power_secs=1,
            api_call_interval=1,  # Trigger live update on first opportunity
            output_handlers=[],  # Clear any default handlers like FileOutput
            save_to_file=False,  # Ensure no file is created by default
            save_to_api=False,
            # Config file is mocked by get_custom_mock_open in setUp
        )

        # --- Test Logic ---
        tracker.start_task("my_test_task")
        # Simulate some work or time passing if necessary, though energy is mocked.
        # time.sleep(0.1) # Not strictly needed due to mocking

        task_data = tracker.stop_task()
        # In stop_task:
        # 1. _measure_power_and_energy() is called MANUALLY.
        #    - mock_cpu_measure and mock_ram_measure are called.
        #    - _total_energies get cpu_energy_val_task and ram_energy_val_task added.
        #    - _measure_occurrence becomes 1.
        #    - Since api_call_interval is 1, live update path IS triggered if _measure_occurrence >= api_call_interval:
        #        - _prepare_emissions_data() called (gets totals including task energy).
        #        - _compute_emissions_delta() called. This updates _previous_emissions.
        # 2. Back in stop_task, after _measure_power_and_energy():
        #    - _prepare_emissions_data() called again (gets same totals).
        #    - The NEW logic computes delta using _active_task_emissions_at_start.
        #    - The global _previous_emissions is then updated again using current totals by another _compute_emissions_delta call.

        # --- Assertions ---
        self.assertIsNotNone(task_data, "Task data should not be None")

        self.assertGreater(task_data.cpu_energy, 0, "CPU energy should be non-zero")
        self.assertAlmostEqual(
            task_data.cpu_energy,
            cpu_energy_val_task,
            places=7,
            msg="CPU energy does not match expected task energy",
        )

        self.assertGreater(task_data.ram_energy, 0, "RAM energy should be non-zero")
        self.assertAlmostEqual(
            task_data.ram_energy,
            ram_energy_val_task,
            places=7,
            msg="RAM energy does not match expected task energy",
        )

        expected_total_energy = cpu_energy_val_task + ram_energy_val_task
        self.assertGreater(
            task_data.energy_consumed, 0, "Total energy consumed should be non-zero"
        )
        self.assertAlmostEqual(
            task_data.energy_consumed,
            expected_total_energy,
            places=7,
            msg="Total energy consumed does not match sum of components",
        )

        # Verify mocks were called as expected
        # They are called once in _measure_power_and_energy inside stop_task
        mock_cpu_measure.assert_called_once()
        mock_ram_measure.assert_called_once()

    @responses.activate
    def test_carbon_tracker_offline_context_manager(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        with OfflineEmissionsTracker(
            country_iso_code="USA", output_dir=self.temp_path
        ) as tracker:
            heavy_computation(run_time_secs=2)

        emissions_df = pd.read_csv(self.emissions_file_path)

        self.assertEqual("United States", emissions_df["country_name"].values[0])
        self.assertEqual("USA", emissions_df["country_iso_code"].values[0])
        self.assertIsInstance(tracker.final_emissions, float)
