from prometheus_client import CollectorRegistry, Gauge

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
