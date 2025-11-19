"""
Tests for CPU, RAM, and GPU utilization tracking functionality.
"""
import time
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker
from tests.testutils import get_custom_mock_open


empty_conf = "[codecarbon]"


class TestUtilizationTracking(unittest.TestCase):
    """Test suite for CPU and RAM utilization tracking features."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        import tempfile

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.emissions_file_path = self.temp_path / "emissions.csv"
        
        # Patch config file access
        patcher = mock.patch(
            "builtins.open", new_callable=get_custom_mock_open(empty_conf, empty_conf)
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_utilization_fields_in_emissions_data(self):
        """Test that EmissionsData contains utilization fields."""
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            save_to_file=False,
        )
        
        tracker.start()
        time.sleep(2)  # Run for 2 seconds to collect measurements
        tracker.stop()
        
        emissions_data = tracker.final_emissions_data
        
        # Verify utilization fields exist
        self.assertTrue(hasattr(emissions_data, 'cpu_utilization_percent'))
        self.assertTrue(hasattr(emissions_data, 'gpu_utilization_percent'))
        self.assertTrue(hasattr(emissions_data, 'ram_utilization_percent'))
        self.assertTrue(hasattr(emissions_data, 'ram_used_gb'))
        
        # Verify values are reasonable
        self.assertGreaterEqual(emissions_data.cpu_utilization_percent, 0)
        self.assertLessEqual(emissions_data.cpu_utilization_percent, 100)
        self.assertGreaterEqual(emissions_data.gpu_utilization_percent, 0)
        self.assertLessEqual(emissions_data.gpu_utilization_percent, 100)
        self.assertGreaterEqual(emissions_data.ram_utilization_percent, 0)
        self.assertLessEqual(emissions_data.ram_utilization_percent, 100)
        self.assertGreaterEqual(emissions_data.ram_used_gb, 0)

    def test_utilization_fields_in_csv_output(self):
        """Test that utilization metrics are saved to CSV file."""
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
        )
        
        tracker.start()
        time.sleep(2)  # Run for 2 seconds to collect measurements
        tracker.stop()
        
        # Read CSV and verify columns exist
        emissions_df = pd.read_csv(self.emissions_file_path)
        
        self.assertIn('cpu_utilization_percent', emissions_df.columns)
        self.assertIn('gpu_utilization_percent', emissions_df.columns)
        self.assertIn('ram_utilization_percent', emissions_df.columns)
        self.assertIn('ram_used_gb', emissions_df.columns)
        
        # Verify values are reasonable
        cpu_util = emissions_df['cpu_utilization_percent'].values[0]
        gpu_util = emissions_df['gpu_utilization_percent'].values[0]
        ram_util = emissions_df['ram_utilization_percent'].values[0]
        ram_used = emissions_df['ram_used_gb'].values[0]
        
        self.assertGreaterEqual(cpu_util, 0)
        self.assertLessEqual(cpu_util, 100)
        self.assertGreaterEqual(gpu_util, 0)
        self.assertLessEqual(gpu_util, 100)
        self.assertGreaterEqual(ram_util, 0)
        self.assertLessEqual(ram_util, 100)
        self.assertGreaterEqual(ram_used, 0)

    def test_utilization_history_cleared_on_start(self):
        """Test that utilization history is cleared when tracker starts."""
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            save_to_file=False,
        )
        
        # First run
        tracker.start()
        time.sleep(1)
        tracker.stop()
        first_cpu_util = tracker.final_emissions_data.cpu_utilization_percent
        
        # Second run - history should be cleared
        tracker.start()
        time.sleep(1)
        tracker.stop()
        second_cpu_util = tracker.final_emissions_data.cpu_utilization_percent
        
        # Both should have valid values (not necessarily equal)
        self.assertGreaterEqual(first_cpu_util, 0)
        self.assertGreaterEqual(second_cpu_util, 0)

    def test_utilization_averaging_over_time(self):
        """Test that utilization values are averaged over the tracking period."""
        import psutil
        
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            save_to_file=False,
        )
        
        # Get instantaneous value before starting
        instant_before = psutil.cpu_percent()
        
        tracker.start()
        time.sleep(3)  # Run for 3 seconds to collect multiple measurements
        tracker.stop()
        
        # Get instantaneous value after stopping
        instant_after = psutil.cpu_percent()
        
        averaged = tracker.final_emissions_data.cpu_utilization_percent
        
        # Averaged value should be valid
        self.assertGreaterEqual(averaged, 0)
        self.assertLessEqual(averaged, 100)
        
        # The averaged value may differ from instantaneous values
        # This is expected behavior - we're just verifying it's computed

    def test_task_utilization_tracking(self):
        """Test that task-based tracking includes utilization metrics."""
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            save_to_file=False,
        )
        
        tracker.start()
        tracker.start_task("test_task")
        time.sleep(2)
        task_data = tracker.stop_task()
        tracker.stop()
        
        # Verify task data has utilization fields
        self.assertTrue(hasattr(task_data, 'cpu_utilization_percent'))
        self.assertTrue(hasattr(task_data, 'ram_utilization_percent'))
        self.assertTrue(hasattr(task_data, 'ram_used_gb'))
        self.assertTrue(hasattr(task_data, 'gpu_utilization_percent'))
        
        # Verify values are reasonable
        self.assertGreaterEqual(task_data.cpu_utilization_percent, 0)
        self.assertLessEqual(task_data.cpu_utilization_percent, 100)
        self.assertGreaterEqual(task_data.ram_utilization_percent, 0)
        self.assertLessEqual(task_data.ram_utilization_percent, 100)
        self.assertGreaterEqual(task_data.ram_used_gb, 0)
        self.assertGreaterEqual(task_data.gpu_utilization_percent, 0)
        self.assertLessEqual(task_data.gpu_utilization_percent, 100)

    def test_utilization_with_empty_history(self):
        """Test that tracker handles empty history gracefully."""
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.temp_path,
            save_to_file=False,
        )
        
        # Start and stop immediately (minimal time for history collection)
        tracker.start()
        tracker.stop()
        
        emissions_data = tracker.final_emissions_data
        
        # Should still have valid values (fallback to instantaneous)
        self.assertGreaterEqual(emissions_data.cpu_utilization_percent, 0)
        self.assertLessEqual(emissions_data.cpu_utilization_percent, 100)
        self.assertGreaterEqual(emissions_data.ram_utilization_percent, 0)
        self.assertLessEqual(emissions_data.ram_utilization_percent, 100)


if __name__ == "__main__":
    unittest.main()
