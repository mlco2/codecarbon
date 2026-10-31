import os
import tempfile
import time
import unittest

import pandas as pd

from codecarbon.emissions_tracker import OfflineEmissionsTracker


def light_computation(run_time_secs: int = 1):
    end_time: float = time.perf_counter() + run_time_secs
    while time.perf_counter() < end_time:
        pass


class TestForceConstantMode(unittest.TestCase):
    def setUp(self) -> None:
        self.emissions_file = "emissions-test-TestForceConstantMode.csv"
        self.emissions_path = tempfile.gettempdir()
        self.emissions_file_path = os.path.join(
            self.emissions_path, self.emissions_file
        )
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def tearDown(self) -> None:
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

    def _run_tracker(self, **kwargs) -> pd.DataFrame:
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_mode_constant=True,
            **kwargs,
        )
        tracker.start()
        light_computation(run_time_secs=1)
        emissions = tracker.stop()

        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        return pd.read_csv(self.emissions_file_path)

    def test_force_constant_mode(self):
        df = self._run_tracker()
        self.assertGreater(df["cpu_power"].iloc[0], 0)

    def test_force_constant_mode_with_custom_cpu_power(self):
        df = self._run_tracker(force_cpu_power=200)
        # Constant mode assumes the CPU draws 50% of its TDP
        self.assertEqual(df["cpu_power"].iloc[0], 100)

    def test_force_constant_mode_takes_precedence_over_cpu_load(self):
        df = self._run_tracker(force_cpu_power=200, force_mode_cpu_load=True)
        self.assertEqual(df["cpu_power"].iloc[0], 100)


if __name__ == "__main__":
    unittest.main()
