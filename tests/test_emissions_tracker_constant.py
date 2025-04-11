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
    track_emissions,
)


def heavy_computation(run_time_secs: int = 3):
    end_time: float = (
        time.perf_counter() + run_time_secs
    )  # Run for `run_time_secs` seconds
    while time.perf_counter() < end_time:
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

    @mock.patch.object(cpu.TDP, "_get_cpu_power_from_registry")
    @mock.patch.object(cpu, "is_psutil_available")
    def test_carbon_tracker_offline_constant_force_cpu_power(
        self, mock_tdp, mock_psutil
    ):
        # Same as test_carbon_tracker_offline_constant test but this time forcing the default cpu power
        USER_INPUT_CPU_POWER = 1_000
        # Mock the output of tdp
        mock_tdp.return_value = None
        mock_psutil.return_value = False
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_cpu_power=USER_INPUT_CPU_POWER,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        # Assert the content stored. cpu_power should be 50% of input TDP
        assertdf = pd.read_csv(self.emissions_file_path)
        self.assertEqual(USER_INPUT_CPU_POWER / 2, assertdf["cpu_power"][0])

    @mock.patch.object(cpu.TDP, "_get_cpu_power_from_registry")
    @mock.patch.object(cpu, "is_psutil_available")
    def test_carbon_tracker_offline_load_force_cpu_power(self, mock_tdp, mock_psutil):
        # Same as test_carbon_tracker_offline_constant test but this time forcing the default cpu power
        USER_INPUT_CPU_POWER = 1_000
        # Mock the output of tdp
        mock_tdp.return_value = 500
        mock_psutil.return_value = True
        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
            force_cpu_power=USER_INPUT_CPU_POWER,
        )
        tracker.start()
        heavy_computation(run_time_secs=1)
        emissions = tracker.stop()
        assert isinstance(emissions, float)
        self.assertNotEqual(emissions, 0.0)
        # Assert the content stored. cpu_power should be a random value between 0 and 250
        assertdf = pd.read_csv(self.emissions_file_path)
        self.assertLess(assertdf["cpu_power"][0], USER_INPUT_CPU_POWER / 4)

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

    def test_carbon_tracker_offline_region_error(self):
        # Test errors when unknown information is given to the offline tracker
        from codecarbon.external.geography import CloudMetadata

        tracker = OfflineEmissionsTracker(
            country_iso_code="USA",
            cloud_provider="aws",
            cloud_region="us-east-1",
            output_dir=self.emissions_path,
            output_file=self.emissions_file,
        )
        tracker.start()
        tracker._measure_power_and_energy()
        cloud: CloudMetadata = tracker._get_cloud_metadata()

        try:
            with self.assertRaises(ValueError) as context:
                tracker._emissions.get_cloud_country_iso_code(cloud)
            self.assertTrue(
                "Unable to find country ISO Code" in context.exception.args[0]
            )

            with self.assertRaises(ValueError) as context:
                tracker._emissions.get_cloud_geo_region(cloud)
            self.assertTrue(
                "Unable to find State/City name for " in context.exception.args[0]
            )

            with self.assertRaises(ValueError) as context:
                tracker._emissions.get_cloud_country_name(cloud)
            self.assertTrue("Unable to find country name" in context.exception.args[0])

        finally:
            tracker.stop()
