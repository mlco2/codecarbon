import dataclasses
import os

from prometheus_client import push_to_gateway
from prometheus_client.exposition import basic_auth_handler

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output_method import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.metrics.prometheus.metrics import (
    cpu_energy_gauge,
    cpu_power_gauge,
    duration_gauge,
    emissions_gauge,
    emissions_rate_gauge,
    energy_consumed_gauge,
    gpu_energy_gauge,
    gpu_power_gauge,
    ram_energy_gauge,
    ram_power_gauge,
    registry,
)


class PrometheusOutput(BaseOutput):
    """
    Send emissions data to prometheus pushgateway
    """

    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url

    def out(self, data: EmissionsData):
        try:
            self.add_emission(dataclasses.asdict(data))
        except Exception as e:
            logger.error(e, exc_info=True)

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
