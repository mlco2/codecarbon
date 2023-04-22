from prometheus_client import CollectorRegistry, Gauge

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
    "gpu_model",
    "tracking_mode",
]

duration_gauge = Gauge(
    "codecarbon_duration",
    "TODO: Add description of this metric",
    registry=registry,
)
emissions_gauge = Gauge(
    "codecarbon_emissions",
    "TODO: Add description of this metric",
    registry=registry,
)
emissions_rate_gauge = Gauge(
    "codecarbon_emissions_rate_gauge",
    "TODO: Add description of this metric",
    registry=registry,
)
cpu_power_gauge = Gauge(
    "codecarbon_cpu_power",
    "TODO: Add description of this metric",
    registry=registry,
)
gpu_power_gauge = Gauge(
    "codecarbon_gpu_power",
    "TODO: Add description of this metric",
    registry=registry,
)
ram_power_gauge = Gauge(
    "codecarbon_ram_power",
    "TODO: Add description of this metric",
    registry=registry,
)
cpu_energy_gauge = Gauge(
    "codecarbon_cpu_energy",
    "TODO: Add description of this metric",
    registry=registry,
)
gpu_energy_gauge = Gauge(
    "codecarbon_gpu_energy",
    "TODO: Add description of this metric",
    registry=registry,
)
ram_energy_gauge = Gauge(
    "codecarbon_ram_energy",
    "TODO: Add description of this metric",
    registry=registry,
)
energy_consumed_gauge = Gauge(
    "codecarbon_energy_consumed",
    "TODO: Add description of this metric",
    registry=registry,
)
cpu_count_gauge = Gauge(
    "codecarbon_cpu_count",
    "TODO: Add description of this metric",
    registry=registry,
)
gpu_count_gauge = Gauge(
    "codecarbon_gpu_count",
    "TODO: Add description of this metric",
    registry=registry,
)
ram_total_size_gauge = Gauge(
    "codecarbon_ram_total_size",
    "TODO: Add description of this metric",
    registry=registry,
)
