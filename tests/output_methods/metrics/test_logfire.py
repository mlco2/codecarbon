import sys
import unittest
from unittest.mock import patch

import logfire

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.metrics.logfire import LogfireOutput


class TestLogfireOutput(unittest.TestCase):
    def setUp(self):
        self.emissions_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test_project",
            run_id="test_run_id",
            experiment_id="test_experiment_id",
            duration=10,
            emissions=0.5,
            emissions_rate=0.05,
            cpu_power=20,
            gpu_power=30,
            ram_power=5,
            cpu_energy=200,
            gpu_energy=300,
            ram_energy=50,
            energy_consumed=550,
            water_consumed=0.1,
            country_name="Testland",
            country_iso_code="TS",
            region="Test Region",
            cloud_provider="Test Cloud",
            cloud_region="test-cloud-1",
            os="TestOS",
            python_version="3.8",
            codecarbon_version="2.0",
            cpu_count=4,
            cpu_model="Test CPU",
            gpu_count=1,
            gpu_model="Test GPU",
            longitude=0,
            latitude=0,
            ram_total_size=16,
            tracking_mode="machine",
            on_cloud="true",
            pue=1.5,
            wue=0.5,
        )

        self.configure_patcher = patch("logfire.configure")
        self.mock_configure = self.configure_patcher.start()
        self.mock_configure.return_value = logfire.configure(send_to_logfire=False)
        self.addCleanup(self.configure_patcher.stop)

    @patch.dict(sys.modules, {"logfire": None})
    def test_logfire_import_error(self):
        with self.assertRaises(ImportError):
            LogfireOutput()

    def test_logfire_initialization(self):
        LogfireOutput()

    def _check_output_is_not_empty(self, logfire_output):
        self.assertIsNotNone(logfire_output.duration)
        self.assertIsNotNone(logfire_output.emissions)
        self.assertIsNotNone(logfire_output.emissions_rate)
        self.assertIsNotNone(logfire_output.cpu_power)
        self.assertIsNotNone(logfire_output.gpu_power)
        self.assertIsNotNone(logfire_output.ram_power)
        self.assertIsNotNone(logfire_output.cpu_energy)
        self.assertIsNotNone(logfire_output.gpu_energy)
        self.assertIsNotNone(logfire_output.ram_energy)
        self.assertIsNotNone(logfire_output.energy_consumed)

    def test_logfire_out(self):
        logfire_output = LogfireOutput()
        logfire_output.out(self.emissions_data, self.emissions_data)
        self._check_output_is_not_empty(logfire_output)

    def test_logfire_live_out(self):
        logfire_output = LogfireOutput()
        logfire_output.live_out(self.emissions_data, self.emissions_data)
        self._check_output_is_not_empty(logfire_output)
