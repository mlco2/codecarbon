import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from codecarbon.emissions_tracker import OfflineEmissionsTracker
from tests.testutils import get_custom_mock_open, get_test_data_source


def heavy_computation(run_time_secs: float = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        pass


empty_conf = "[codecarbon]"


class TestOfflineEmissionsTracker(unittest.TestCase):
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

    def test_offline_tracker(self):
        tracker = OfflineEmissionsTracker(output_file=self.emissions_file_path)
        tracker.start()
        heavy_computation(run_time_secs=2)
        tracker.stop()

        emissions_df = pd.read_csv(self.emissions_file_path)

        self.assertGreater(emissions_df["emissions"].values[0], 0.0)
        # Check NaN values
        self.assertNotEqual(
            emissions_df["country_name"].values[0],
            emissions_df["country_name"].values[0],
        )
        self.assertNotEqual(
            emissions_df["country_iso_code"].values[0],
            emissions_df["country_iso_code"].values[0],
        )

    def test_offline_tracker_task(self):
        tracker = OfflineEmissionsTracker()
        tracker.start_task()
        heavy_computation(run_time_secs=2)
        task_emission_data = tracker.stop_task()

        self.assertGreater(task_emission_data.emissions, 0.0)
        self.assertEqual(task_emission_data.country_name, None)
