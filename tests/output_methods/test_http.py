import unittest
from unittest.mock import MagicMock, patch

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
        self.http_output = HTTPOutput(endpoint_url=self.url)

    @patch(
        "codecarbon.output_methods.http.requests.post",
        return_value=MagicMock(status_code=201),
    )
    def test_http_output_post_success(self, mock_post):
        self.http_output.out(self.emissions_data, self.emissions_data)

        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args[0][0], self.url)

    @patch("codecarbon.output_methods.http.logger.warning")
    @patch(
        "codecarbon.output_methods.http.requests.post",
        return_value=MagicMock(status_code=418),
    )
    def test_http_output_post_unexpected_status(self, mock_post, mock_logger):
        self.http_output.out(self.emissions_data, self.emissions_data)

        mock_post.assert_called_once()
        mock_logger.assert_called_once()

    @patch("codecarbon.output_methods.http.logger.error")
    @patch(
        "codecarbon.output_methods.http.requests.post",
        side_effect=Exception("Test exception"),
    )
    def test_http_output_post_exception(self, mock_post, mock_logger):
        self.http_output.out(self.emissions_data, self.emissions_data)
        mock_post.assert_called_once()
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

    def test_codecarbon_api_task_out(self):
        from codecarbon.output_methods.emissions_data import TaskEmissionsData

        api_output = CodeCarbonAPIOutput(
            endpoint_url=self.url,
            experiment_id=self.experiment_id,
            api_key=self.api_key,
            conf=None,
        )
        task_data = TaskEmissionsData(
            task_name="GET /predict",
            timestamp=self.emissions_data.timestamp,
            project_name=self.emissions_data.project_name,
            run_id=self.emissions_data.run_id,
            duration=2.0,
            emissions=self.emissions_data.emissions,
            emissions_rate=self.emissions_data.emissions_rate,
            cpu_power=self.emissions_data.cpu_power,
            gpu_power=self.emissions_data.gpu_power,
            ram_power=self.emissions_data.ram_power,
            cpu_energy=self.emissions_data.cpu_energy,
            gpu_energy=self.emissions_data.gpu_energy,
            ram_energy=self.emissions_data.ram_energy,
            energy_consumed=self.emissions_data.energy_consumed,
            water_consumed=self.emissions_data.water_consumed,
            country_name=self.emissions_data.country_name,
            country_iso_code=self.emissions_data.country_iso_code,
            region=self.emissions_data.region,
            cloud_provider=self.emissions_data.cloud_provider,
            cloud_region=self.emissions_data.cloud_region,
            os=self.emissions_data.os,
            python_version=self.emissions_data.python_version,
            codecarbon_version=self.emissions_data.codecarbon_version,
            cpu_count=self.emissions_data.cpu_count,
            cpu_model=self.emissions_data.cpu_model,
            gpu_count=self.emissions_data.gpu_count,
            gpu_model=self.emissions_data.gpu_model,
            longitude=self.emissions_data.longitude,
            latitude=self.emissions_data.latitude,
            ram_total_size=self.emissions_data.ram_total_size,
            tracking_mode=self.emissions_data.tracking_mode,
            on_cloud=self.emissions_data.on_cloud,
        )
        api_output.task_out([task_data], "test_experiment")
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
