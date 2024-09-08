import os
import tempfile
import time
import unittest

import pandas as pd

from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)


def heavy_computation(run_time_secs: int = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        pass


class TestCarbonTrackerFlush(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestCarbonTrackerFlush"
        self.emissions_file = "emissions-test-TestCarbonTrackerFlush.csv"
        self.emissions_path = tempfile.gettempdir()
        self.emissions_file_path = os.path.join(
            self.emissions_path, self.emissions_file
        )
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def tearDown(self) -> None:
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def test_carbon_tracker_online_flush(self):
        tracker = EmissionsTracker(
            output_dir=self.emissions_path, output_file=self.emissions_file
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        tracker.flush()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()

        if not isinstance(emissions, float):
            print(emissions)

        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_output_file(self.emissions_file_path)

    def test_carbon_tracker_offline_flush(self):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        tracker.flush()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_output_file(self.emissions_file_path)

    def test_decorator_flush(self):
        @track_emissions(
            project_name=self.project_name,
            experiment_id="test",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
        )
        def dummy_train_model():
            # I don't know how to call flush() in decorator mode
            return 42

        res = dummy_train_model()
        self.assertEqual(res, 42)
        self.verify_experiment_id_presence()

        self.verify_output_file(self.emissions_file_path, 2)

    def verify_experiment_id_presence(self) -> None:
        assert os.path.isfile(self.emissions_file_path)
        emissions_df = pd.read_csv(self.emissions_file_path)
        print(
            emissions_df[
                ["project_name", "experiment_id", "country_iso_code", "country_name"]
            ]
        )
        self.assertEqual("test", emissions_df["experiment_id"].values[0])

    def verify_output_file(self, file_path: str, expected_lines=3) -> None:
        with open(file_path, "r") as f:
            lines = [line.rstrip() for line in f]
        assert len(lines) == expected_lines
