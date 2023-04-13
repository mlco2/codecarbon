import os
import tempfile
import time
import unittest

from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)


def heavy_computation(run_time_secs: int = 3):
    end_time: float = time.time() + run_time_secs  # Run for `run_time_secs` seconds
    while time.time() < end_time:
        pass


class TestCarbonTrackerConstant(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestCarbonTrackerConstant"
        self.emissions_file = "emissions-test-TestCarbonTrackerConstant.csv"
        self.emissions_path = tempfile.gettempdir()
        self.emissions_file_path = os.path.join(
            self.emissions_path, self.emissions_file
        )
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def tearDown(self) -> None:
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def test_carbon_tracker_online_constant(self):
        tracker = EmissionsTracker(
            output_dir=self.emissions_path, output_file=self.emissions_file
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_output_file(self.emissions_file_path)

    def test_carbon_tracker_offline_constant(self):
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.assertAlmostEqual(emissions, 6.262572537957655e-05, places=2)
        self.verify_output_file(self.emissions_file_path)

    def test_carbon_tracker_offline_constant_default_cpu_power(self):
        # Same as test_carbon_tracker_offline_constant test but this time forcing the default cpu power
        USER_INPUT_CPU_POWER = 1000
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            default_cpu_power=USER_INPUT_CPU_POWER,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        # Assert the content stored. cpu_power should be 50% of input TDP
        import pandas as pd

        assertdf = pd.read_csv(self.emissions_file_path)
        self.assertEqual(USER_INPUT_CPU_POWER / 2, assertdf["cpu_power"][0])

    def test_decorator_constant(self):
        @track_emissions(
            project_name=self.project_name,
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
        )
        def dummy_train_model():
            return 42

        dummy_train_model()

        self.verify_output_file(self.emissions_file_path)

    def verify_output_file(self, file_path: str) -> None:
        with open(file_path, "r") as f:
            lines = [line.rstrip() for line in f]
        assert len(lines) == 2
