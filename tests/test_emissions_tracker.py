import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import requests
import responses

from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)
from codecarbon.external.geography import CloudMetadata
from tests.testdata import GEO_METADATA_CANADA, TWO_GPU_DETAILS_RESPONSE
from tests.testutils import get_custom_mock_open, get_test_data_source


def heavy_computation(run_time_secs: float = 3):
    end_time: float = time.time() + run_time_secs  # Run for `run_time_secs` seconds
    while time.time() < end_time:
        pass


empty_conf = "[codecarbon]"


@mock.patch("codecarbon.core.gpu.is_gpu_details_available", return_value=True)
@mock.patch(
    "codecarbon.external.hardware.get_gpu_details",
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
        self.temp_dir.cleanup()

    @responses.activate
    def test_carbon_tracker_TWO_GPU_PRIVATE_INFRA_CANADA(
        self,
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
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
        emissions = tracker.stop().emissions

        # THEN
        self.assertGreaterEqual(
            mocked_get_gpu_details.call_count, 2
        )  # at least 2 times in 5 seconds + once for init >= 3
        self.assertEqual(1, mocked_is_gpu_details_available.call_count)
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
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        # GIVEN

        def raise_timeout_exception(*args, **kwargs):
            raise requests.exceptions.Timeout()

        mocked_requests_get.side_effect = raise_timeout_exception

        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        # WHEN
        tracker.start()
        heavy_computation(run_time_secs=2)
        emissions = tracker.stop().emissions
        self.assertEqual(1, mocked_requests_get.call_count)
        self.assertIsInstance(emissions, float)
        self.assertAlmostEqual(1.1037980397280433e-05, emissions, places=2)

    def test_graceful_start_failure(
        self,
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
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
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
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
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
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
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
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
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        # WHEN

        @track_emissions(offline=True)
        def dummy_train_model():
            return 42

        self.assertRaises(Exception, dummy_train_model)

    def test_decorator_OFFLINE_WITH_LOC_ARGS(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        # GIVEN

        @track_emissions(
            offline=True,
            country_iso_code="CAN",
            project_name=self.project_name,
            output_dir=self.temp_path,
        )
        def dummy_train_model():
            return 42

        dummy_train_model()
        self.verify_output_file(self.emissions_file_path, 2)

    def test_decorator_OFFLINE_WITH_CLOUD_ARGS(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        # GIVEN

        @track_emissions(
            offline=True,
            cloud_provider="gcp",
            cloud_region="us-central1",
            output_dir=self.temp_path,
        )
        def dummy_train_model():
            return 42

        dummy_train_model()
        self.verify_output_file(self.emissions_file_path, 2)

    def test_offline_tracker_country_name(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA", output_dir=self.temp_path
        )
        tracker.start()
        heavy_computation(run_time_secs=2)
        tracker.stop()

        emissions_df = pd.read_csv(self.emissions_file_path)

        self.assertEqual("United States", emissions_df["country_name"].values[0])
        self.assertEqual("USA", emissions_df["country_iso_code"].values[0])

    def test_offline_tracker_invalid_headers(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA", output_dir=self.temp_path
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
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA", output_dir=self.temp_path
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
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
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
        self.assertEqual(1, mocked_is_gpu_details_available.call_count)
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
            "https://get.geojs.io/v1/ip/geo.json", responses.calls[0].request.url
        )
        self.assertIsInstance(tracker.final_emissions_data.emissions, float)
        self.assertAlmostEqual(
            tracker.final_emissions_data.emissions, 6.262572537957655e-05, places=2
        )

    @responses.activate
    def test_carbon_tracker_offline_context_manager(
        self,
        mocked_env_cloud_details,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        with OfflineEmissionsTracker(
            country_iso_code="USA", output_dir=self.temp_path
        ) as tracker:
            heavy_computation(run_time_secs=2)

        emissions_df = pd.read_csv(self.emissions_file_path)

        self.assertEqual("United States", emissions_df["country_name"].values[0])
        self.assertEqual("USA", emissions_df["country_iso_code"].values[0])
        self.assertIsInstance(tracker.final_emissions_data.emissions, float)

    def test_offline_tracker_start_stop_start_stop(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):
        tracker = OfflineEmissionsTracker(
            measure_power_secs=2, country_iso_code="USA", output_dir=self.temp_path
        )

        tracker.start()
        heavy_computation(run_time_secs=5)
        tracker.stop()

        tracker.start()
        heavy_computation(run_time_secs=5)
        tracker.stop()

    def test_online_tracker_start_stop_start_stop(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):

        tracker = EmissionsTracker(measure_power_secs=1, save_to_file=False)

        tracker.start()
        heavy_computation(run_time_secs=1.2)
        tracker.stop()

        tracker.start()
        heavy_computation(run_time_secs=1.2)
        tracker.stop()

    def test_tracker_resume(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):

        run_time = 3
        pause_time = 2
        keys = [
            "timestamp",
            "project_name",
            "duration",
            "emissions",
            "energy_consumed",
        ]
        for tracker, name in [
            (
                OfflineEmissionsTracker(
                    measure_power_secs=1,
                    country_iso_code="USA",
                    output_dir=self.temp_path,
                    output_file="resume_emissions_offline.csv",
                ),
                "resume_emissions_offline.csv",
            ),
            (
                EmissionsTracker(
                    measure_power_secs=1,
                    output_dir=self.temp_path,
                    output_file="resume_emissions.csv",
                ),
                "resume_emissions.csv",
            ),
        ]:

            with self.subTest(tracker=tracker):

                path = self.temp_path / name

                tracker.start()
                heavy_computation(run_time_secs=run_time)
                first_data = tracker.stop()
                df1 = pd.read_csv(path)

                heavy_computation(run_time_secs=pause_time)

                tracker.start()
                heavy_computation(run_time_secs=run_time)
                second_data = tracker.stop()
                df2 = pd.read_csv(path)

                dict_df = dict(df2.iloc[-1].fillna(""))
                dict_data = dict(second_data.values)

                self.assertAlmostEqual(second_data.duration, 2 * run_time, delta=0.1)
                self.assertGreater(second_data.emissions, first_data.emissions)
                self.assertGreater(
                    second_data.energy_consumed, first_data.energy_consumed
                )
                self.assertEqual(len(df1), len(df2))
                for k in keys:
                    if isinstance(dict_df[k], (float, int)):
                        self.assertAlmostEqual(dict_df[k], dict_data[k])
                    else:
                        self.assertEqual(dict_df[k], dict_data[k])

    def test_tracker_resume_update_row(
        self,
        mocked_get_cloud_metadata,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
        mock_setup_intel_cli,
        mock_log_values,
    ):

        n_trackers = 3
        n_loops = 3

        trackers = [
            EmissionsTracker(
                measure_power_secs=1,
                output_dir=self.temp_path,
                output_file="resume_emissions_update_row.csv",
                log_level="error",
            )
            for _ in range(n_trackers)
        ]

        for i in range(n_loops):

            print("\nLoop", i)

            for t, tracker in enumerate(trackers):
                print("Tracker", t)
                tracker.start()
                heavy_computation(2)
                tracker.stop()

            id_tracker = np.random.randint(0, n_trackers)
            tracker = trackers[id_tracker]
            keys = [
                "timestamp",
                "project_name",
                "duration",
                "emissions",
                "energy_consumed",
            ]
            path = self.temp_path / "resume_emissions_update_row.csv"

            df = pd.read_csv(path)

            self.assertEqual(len(df), len(trackers))

            dict_df = dict(df.iloc[id_tracker])
            dict_data = dict(trackers[id_tracker].final_emissions_data.values)

            for k in keys:
                if isinstance(dict_df[k], (float, int)):
                    self.assertAlmostEqual(dict_df[k], dict_data[k])
                else:
                    self.assertEqual(dict_df[k], dict_data[k])
