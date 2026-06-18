import unittest
from unittest.mock import MagicMock, patch

import requests_mock

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.http import CodeCarbonAPIOutput, HTTPOutput


class TestHTTPOutput(unittest.TestCase):
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
        self.url = "http://test.com/emissions"

    @patch("codecarbon.output_methods.http.get_http_session")
    def test_http_output_post_success(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.post.return_value = MagicMock(status_code=201)
        mock_get_session.return_value = mock_session
        http_output = HTTPOutput(endpoint_url=self.url)

        http_output.out(self.emissions_data, self.emissions_data)

        mock_session.post.assert_called_once()
        self.assertEqual(mock_session.post.call_args[0][0], self.url)

    @patch("codecarbon.output_methods.http.logger.warning")
    @patch("codecarbon.output_methods.http.get_http_session")
    def test_http_output_post_unexpected_status(self, mock_get_session, mock_logger):
        mock_session = MagicMock()
        mock_session.post.return_value = MagicMock(status_code=418)
        mock_get_session.return_value = mock_session
        http_output = HTTPOutput(endpoint_url=self.url)

        http_output.out(self.emissions_data, self.emissions_data)

        mock_session.post.assert_called_once()
        mock_logger.assert_called_once()

    @patch("codecarbon.output_methods.http.logger.error")
    @patch("codecarbon.output_methods.http.get_http_session")
    def test_http_output_post_exception(self, mock_get_session, mock_logger):
        mock_session = MagicMock()
        mock_session.post.side_effect = Exception("Test exception")
        mock_get_session.return_value = mock_session
        http_output = HTTPOutput(endpoint_url=self.url)

        http_output.out(self.emissions_data, self.emissions_data)

        mock_session.post.assert_called_once()
        mock_logger.assert_called_once()


class TestCodeCarbonAPIOutput(unittest.TestCase):
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
        self.url = "http://test.com/emissions"
        self.experiment_id = (
            None  # Set to None so that ApiClient won't attempt a run on initialisation
        )
        self.api_key = "test_key"

        self.add_emission_patcher = patch(
            "codecarbon.output_methods.http.ApiClient.add_emission"
        )
        self.mock_add_emission = self.add_emission_patcher.start()
        self.addCleanup(self.add_emission_patcher.stop)

    def test_codecarbon_api_output_initialization(self):
        CodeCarbonAPIOutput(
            endpoint_url=self.url,
            experiment_id=self.experiment_id,
            api_key=self.api_key,
            conf=None,
        )

    def test_codecarbon_api_live_out(self):
        api_output = CodeCarbonAPIOutput(
            endpoint_url=self.url,
            experiment_id=self.experiment_id,
            api_key=self.api_key,
            conf=None,
        )

        api_output.live_out(None, self.emissions_data)
        self.mock_add_emission.assert_called_once()

    def test_codecarbon_api_live_out_creates_run_when_missing(self):
        conf = {
            "os": "linux",
            "python_version": "3.12",
            "codecarbon_version": "2.0",
            "cpu_count": 4,
            "cpu_model": "CPU",
            "gpu_count": 0,
            "gpu_model": "",
            "longitude": 0.0,
            "latitude": 0.0,
            "region": "EU",
            "provider": "AWS",
            "ram_total_size": 16.0,
            "tracking_mode": "machine",
        }
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/runs",
                json={"id": "run-created"},
                status_code=201,
            )
            m.post("http://test.com/emissions", status_code=201)
            api_output = CodeCarbonAPIOutput(
                endpoint_url="http://test.com",
                experiment_id="exp-1",
                api_key=self.api_key,
                conf=conf,
            )
            api_output.api.run_id = None

            api_output.live_out(None, self.emissions_data)

        self.assertEqual(api_output.api.run_id, "run-created")
        self.assertEqual(api_output.run_id, "run-created")

    @patch("codecarbon.output_methods.http.logger.error")
    def test_codecarbon_live_out_api_call_failure(self, mock_logger):
        self.mock_add_emission.side_effect = Exception("Test exception")
        api_output = CodeCarbonAPIOutput(
            endpoint_url=self.url,
            experiment_id=self.experiment_id,
            api_key=self.api_key,
            conf=None,
        )
        api_output.live_out(None, self.emissions_data)
        mock_logger.assert_called_once()

    def test_codecarbon_api_out(self):
        api_output = CodeCarbonAPIOutput(
            endpoint_url=self.url,
            experiment_id=self.experiment_id,
            api_key=self.api_key,
            conf=None,
        )

        api_output.out(None, self.emissions_data)
        self.mock_add_emission.assert_called_once()

    @patch("codecarbon.output_methods.http.logger.error")
    def test_codecarbon_out_api_call_failure(self, mock_logger):
        self.mock_add_emission.side_effect = Exception("Test exception")
        api_output = CodeCarbonAPIOutput(
            endpoint_url=self.url,
            experiment_id=self.experiment_id,
            api_key=self.api_key,
            conf=None,
        )
        api_output.out(None, self.emissions_data)
        mock_logger.assert_called_once()
