import os
import tempfile
import time
import unittest
from unittest import mock

import pandas as pd

from codecarbon.core import cpu
from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
)


def light_computation(run_time_secs: int = 1):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
        pass


class TestForceConstantMode(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestForceConstantMode"
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

    def test_force_constant_mode_online(self):
        """Test force_mode_constant parameter with online tracker"""
        tracker = EmissionsTracker(
            output_dir=self.emissions_path, 
            output_file=self.emissions_file,
            force_mode_constant=True
        )
        tracker.start()
        light_computation(run_time_secs=1)
        emissions = tracker.stop()
        
        # Check that emissions were calculated
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        
        # Verify output file was created
        self.verify_output_file(self.emissions_file_path)
        
        # Check CSV content shows constant mode
        df = pd.read_csv(self.emissions_file_path)
        # The cpu_power should be a constant value (not varying like in load mode)
        self.assertGreater(df["cpu_power"].iloc[0], 0)

    def test_force_constant_mode_offline(self):
        """Test force_mode_constant parameter with offline tracker"""
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_mode_constant=True
        )
        tracker.start()
        light_computation(run_time_secs=1)
        emissions = tracker.stop()
        
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.verify_output_file(self.emissions_file_path)

    def test_force_constant_mode_with_custom_cpu_power(self):
        """Test force_mode_constant with custom CPU power"""
        custom_cpu_power = 200  # 200W
        tracker = EmissionsTracker(
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_mode_constant=True,
            force_cpu_power=custom_cpu_power
        )
        tracker.start()
        light_computation(run_time_secs=1)
        emissions = tracker.stop()
        
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        
        # Check that the custom CPU power was used
        df = pd.read_csv(self.emissions_file_path)
        # CPU power should be 50% of the TDP (constant mode assumption)
        expected_cpu_power = custom_cpu_power / 2
        self.assertEqual(df["cpu_power"].iloc[0], expected_cpu_power)

    @mock.patch("codecarbon.core.cpu.PSUTIL_AVAILABLE", False)
    @mock.patch("codecarbon.core.util.PSUTIL_AVAILABLE", False)
    def test_force_constant_mode_without_psutil(self):
        """Test that force_mode_constant works when psutil is not available"""
        tracker = EmissionsTracker(
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_mode_constant=True
        )
        tracker.start()
        light_computation(run_time_secs=1)
        emissions = tracker.stop()
        
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.verify_output_file(self.emissions_file_path)

    def test_force_constant_mode_takes_precedence_over_cpu_load(self):
        """Test that force_mode_constant takes precedence over force_mode_cpu_load"""
        tracker = EmissionsTracker(
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_mode_constant=True,
            force_mode_cpu_load=True  # This should be ignored
        )
        tracker.start()
        light_computation(run_time_secs=1)
        emissions = tracker.stop()
        
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        self.verify_output_file(self.emissions_file_path)

    def verify_output_file(self, file_path: str) -> None:
        """Verify that the output CSV file exists and has expected structure"""
        with open(file_path, "r") as f:
            lines = [line.rstrip() for line in f]
        assert len(lines) == 2  # Header + 1 data row
        
        # Check that it's a valid CSV with expected columns
        df = pd.read_csv(file_path)
        expected_columns = ["emissions", "cpu_power", "cpu_energy"]
        for col in expected_columns:
            self.assertIn(col, df.columns)


if __name__ == "__main__":
    unittest.main()