import dataclasses
import os

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import basic_auth_handler

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.metrics.metric_docs import (
    MetricDocumentation,
    cpu_energy_doc,
    cpu_power_doc,
    duration_doc,
    emissions_doc,
    emissions_rate_doc,
    energy_consumed_doc,
    gpu_energy_doc,
    gpu_power_doc,
    ram_energy_doc,
    ram_power_doc,
)

registry = CollectorRegistry()


# TODO: add labelnames
# timestamp: str
# run_id: str
# python_version: str
# longitude: float
# latitude: float
# on_cloud: str = "N"

# TODO: Set up the possible labels
labelnames = [
    "project_name",
    "country_name",
    "country_iso_code",
    "region",
    "cloud_provider",
    "cloud_region",
    "os",
    "codecarbon_version",
    "cpu_model",
    "cpu_count",
    "gpu_model",
    "gpu_count",
    "tracking_mode",
    "ram_total_size",
]


def generate_gauge(metric_doc: MetricDocumentation):
    return Gauge(
        metric_doc.name,
        metric_doc.description,
        labelnames,
        registry=registry,
    )


duration_gauge = generate_gauge(duration_doc)
emissions_gauge = generate_gauge(emissions_doc)
emissions_rate_gauge = generate_gauge(emissions_rate_doc)
cpu_power_gauge = generate_gauge(cpu_power_doc)
gpu_power_gauge = generate_gauge(gpu_power_doc)
ram_power_gauge = generate_gauge(ram_power_doc)
cpu_energy_gauge = generate_gauge(cpu_energy_doc)
gpu_energy_gauge = generate_gauge(gpu_energy_doc)
ram_energy_gauge = generate_gauge(ram_energy_doc)
energy_consumed_gauge = generate_gauge(energy_consumed_doc)


class PrometheusOutput(BaseOutput):
    """
    Send emissions data to prometheus pushgateway
    """

    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url

    def out(self, total: EmissionsData, delta: EmissionsData):
        try:
            self.add_emission(dataclasses.asdict(delta))
        except Exception as e:
            logger.error(e, exc_info=True)

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        self.out(total, delta)

    def _auth_handler(self, url, method, timeout, headers, data):
        username = os.getenv("PROMETHEUS_USERNAME")
        password = os.getenv("PROMETHEUS_PASSWORD")
        return basic_auth_handler(
            url, method, timeout, headers, data, username, password
        )

    def add_emission(self, carbon_emission: dict):
        """
        Send emissions data to push gateway
        """

        # Save the values of the metrics to the local registry
        duration_gauge.labels(carbon_emission["project_name"]).set(
            int(carbon_emission["duration"])
        )
        emissions_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["emissions"]
        )
        emissions_rate_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["emissions_rate"]
        )
        cpu_power_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["cpu_power"]
        )
        gpu_power_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["gpu_power"]
        )
        ram_power_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["ram_power"]
        )
        cpu_energy_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["cpu_energy"]
        )
        gpu_energy_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["gpu_energy"]
        )
        ram_energy_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["ram_energy"]
        )
        energy_consumed_gauge.labels(carbon_emission["project_name"]).set(
            carbon_emission["energy_consumed"]
        )

        # Send the new metric values
        push_to_gateway(
            self.prometheus_url,
            job="codecarbon",
            registry=registry,
            handler=self._auth_handler,
        )
