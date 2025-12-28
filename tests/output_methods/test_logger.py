import logging
import unittest
from unittest.mock import MagicMock, patch

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.logger import GoogleCloudLoggerOutput, LoggerOutput


class TestLoggerOutput(unittest.TestCase):
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
        self.mock_logger = MagicMock()

    def test_logger_output_success(self):
        logger_output = LoggerOutput(self.mock_logger, logging.WARNING)
        logger_output.out(self.emissions_data, None)

        self.mock_logger.log.assert_called_once()

    @patch("codecarbon.output_methods.logger.logger.error")
    def test_logger_output_exception(self, mock_error_logger):
        self.mock_logger.log.side_effect = Exception("Test exception")
        logger_output = LoggerOutput(self.mock_logger)
        logger_output.out(self.emissions_data, None)

        mock_error_logger.assert_called_once()

    def test_logger_live_out_calls_out(self):
        logger_output = LoggerOutput(self.mock_logger)
        logger_output.live_out(self.emissions_data, None)

        self.mock_logger.log.assert_called_once()


class TestGoogleCloudLoggerOutput(unittest.TestCase):
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
        self.mock_logger = MagicMock()

    def test_google_cloud_logger_output_success(self):
        logger_output = GoogleCloudLoggerOutput(self.mock_logger, logging.WARNING)
        logger_output.out(self.emissions_data, None)

        self.mock_logger.log_struct.assert_called_once()

    @patch("codecarbon.output_methods.logger.logger.error")
    def test_google_cloud_logger_output_exception(self, mock_error_logger):
        self.mock_logger.log_struct.side_effect = Exception("Test exception")
        logger_output = GoogleCloudLoggerOutput(self.mock_logger)
        logger_output.out(self.emissions_data, None)

        mock_error_logger.assert_called_once()

    def test_google_cloud_logger_live_out_calls_out(self):
        logger_output = GoogleCloudLoggerOutput(self.mock_logger)
        logger_output.live_out(self.emissions_data, None)

        self.mock_logger.log_struct.assert_called_once()
