import dataclasses
import os

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    delete_from_gateway,
    push_to_gateway,
)
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
    energy_consumed_total_doc,
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


def generate_counter(metric_doc: MetricDocumentation):
    return Counter(
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
energy_consumed_total = generate_counter(energy_consumed_total_doc)


class PrometheusOutput(BaseOutput):
    """
    Send emissions data to prometheus pushgateway
    """

    def __init__(self, prometheus_url: str, job_name: str = "codecarbon"):
        self.prometheus_url = prometheus_url
        self.job_name = job_name

    def exit(self):
        # Cleanup metrics from pushgateway on shutdown, prometheus should already have read them
        # Otherwise they will persist with their last values
        try:
            logger.info("Deleting metrics from Prometheus Pushgateway")
            delete_from_gateway(self.prometheus_url, job=self.job_name)
        except Exception as e:
            logger.error(e, exc_info=True)

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

        # We set label values to '' by default because if we set them to None
        # they get turned into 'None' by gauage.labels(), which is more
        # confusing than an empty string.
        labels = dict.fromkeys(labelnames, "")
        labels["project_name"] = carbon_emission["project_name"]

        for gauge, emission_name in [
            (duration_gauge, "duration"),
            (emissions_gauge, "emissions"),
            (emissions_rate_gauge, "emissions_rate"),
            (cpu_power_gauge, "cpu_power"),
            (gpu_power_gauge, "gpu_power"),
            (ram_power_gauge, "ram_power"),
            (cpu_energy_gauge, "cpu_energy"),
            (gpu_energy_gauge, "gpu_energy"),
            (ram_energy_gauge, "ram_energy"),
            (energy_consumed_gauge, "energy_consumed"),
        ]:
            gauge.labels(**labels).set(carbon_emission[emission_name])

        # Update the total energy consumed counter
        # This is separate from the total values given to self.out(...)
        energy_consumed_total.labels(**labels).inc(carbon_emission["energy_consumed"])

        # Send the new metric values
        push_to_gateway(
            self.prometheus_url,
            job=self.job_name,
            registry=registry,
            handler=self._auth_handler,
        )
