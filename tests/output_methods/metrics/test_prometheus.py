import dataclasses
import importlib
import os
import unittest
from unittest.mock import patch

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.metrics import prometheus

EMISSIONS_DATA = EmissionsData(
    timestamp="2021-01-01T00:00:00",
    project_name="test_project",
    run_id="test_run_id",
    experiment_id="test_experiment_id",
    duration=60,
    emissions=0.1,
    emissions_rate=0.01,
    cpu_power=100,
    gpu_power=200,
    ram_power=50,
    cpu_energy=6000,
    gpu_energy=12000,
    ram_energy=3000,
    energy_consumed=21000,
    water_consumed=0.2,
    country_name="test_country",
    country_iso_code="TC",
    region="test_region",
    cloud_provider="test_provider",
    cloud_region="test_cloud_region",
    os="test_os",
    python_version="3.9",
    codecarbon_version="2.0",
    cpu_model="test_cpu",
    cpu_count=8,
    gpu_model="test_gpu",
    gpu_count=1,
    longitude=0.0,
    latitude=0.0,
    tracking_mode="test_mode",
    ram_total_size=16,
)


class TestPrometheusOutput(unittest.TestCase):
    def setUp(self):
        importlib.reload(prometheus)

    @patch("codecarbon.output_methods.metrics.prometheus.push_to_gateway")
    def test_out_method(self, mock_push_to_gateway):
        output = prometheus.PrometheusOutput("url")
        output.out(total=EMISSIONS_DATA, delta=EMISSIONS_DATA)

    @patch("codecarbon.output_methods.metrics.prometheus.delete_from_gateway")
    def test_exit_method(self, mock_delete):
        output = prometheus.PrometheusOutput("url", job_name="custom_job")
        output.exit()
        mock_delete.assert_called_once_with("url", job="custom_job")

    @patch(
        "codecarbon.output_methods.metrics.prometheus.push_to_gateway",
        side_effect=Exception("Test error"),
    )
    @patch("codecarbon.external.logger.logger.error")
    def test_out_method_handles_exception(
        self, mock_logger_error, mock_push_to_gateway
    ):
        output = prometheus.PrometheusOutput("url")
        output.out(total=EMISSIONS_DATA, delta=EMISSIONS_DATA)

        mock_logger_error.assert_called_once()

    def test_live_out_method_calls_out(self):
        self.test_out_method()

    @patch("codecarbon.output_methods.metrics.prometheus.basic_auth_handler")
    def test_auth_handler(self, mock_basic_auth_handler):
        with patch.dict(
            os.environ,
            {"PROMETHEUS_USERNAME": "user", "PROMETHEUS_PASSWORD": "password"},
        ):
            output = prometheus.PrometheusOutput("url")
            output._auth_handler("url", "method", "timeout", "headers", "data")
            mock_basic_auth_handler.assert_called_with(
                "url", "method", "timeout", "headers", "data", "user", "password"
            )

    @patch("codecarbon.output_methods.metrics.prometheus.push_to_gateway")
    def test_add_emission(self, mock_push_to_gateway):
        output = prometheus.PrometheusOutput("url")
        output.add_emission(dataclasses.asdict(EMISSIONS_DATA))

        mock_push_to_gateway.assert_called_once_with(
            "url",
            job="codecarbon",
            registry=prometheus.registry,
            handler=output._auth_handler,
        )

        # Verify that the gauges have the correct values
        labels = dict.fromkeys(prometheus.labelnames, "")
        labels["project_name"] = "test_project"

        self.assertEqual(
            prometheus.registry.get_sample_value("codecarbon_duration", labels=labels),
            60,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value("codecarbon_emissions", labels=labels),
            0.1,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value(
                "codecarbon_emissions_rate", labels=labels
            ),
            0.01,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value("codecarbon_cpu_power", labels=labels),
            100,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value("codecarbon_gpu_power", labels=labels),
            200,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value("codecarbon_ram_power", labels=labels),
            50,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value(
                "codecarbon_cpu_energy", labels=labels
            ),
            6000,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value(
                "codecarbon_gpu_energy", labels=labels
            ),
            12000,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value(
                "codecarbon_ram_energy", labels=labels
            ),
            3000,
        )
        self.assertEqual(
            prometheus.registry.get_sample_value(
                "codecarbon_energy_consumed", labels=labels
            ),
            21000,
        )
