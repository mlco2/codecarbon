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
    "cpu_count",
    "gpu_model",
    "gpu_count",
    "tracking_mode",
    "ram_total_size",
]

duration_gauge = Gauge(
    "codecarbon_duration",
    "Duration from last measure (s)",
    ["project_name"],
    registry=registry,
)
emissions_gauge = Gauge(
    "codecarbon_emissions",
    "Emissions as CO₂-equivalents [CO₂eq] (kg)",
    ["project_name"],
    registry=registry,
)
emissions_rate_gauge = Gauge(
    "codecarbon_emissions_rate",
    "Emissions divided per duration (Kg/s)",
    ["project_name"],
    registry=registry,
)
cpu_power_gauge = Gauge(
    "codecarbon_cpu_power",
    "CPU power (W)",
    ["project_name"],
    registry=registry,
)
gpu_power_gauge = Gauge(
    "codecarbon_gpu_power",
    "GPU power (W)",
    ["project_name"],
    registry=registry,
)
ram_power_gauge = Gauge(
    "codecarbon_ram_power",
    "RAM power (W)",
    ["project_name"],
    registry=registry,
)
cpu_energy_gauge = Gauge(
    "codecarbon_cpu_energy",
    "Energy used per CPU (kWh)",
    ["project_name"],
    registry=registry,
)
gpu_energy_gauge = Gauge(
    "codecarbon_gpu_energy",
    "Energy used per GPU (kWh)",
    ["project_name"],
    registry=registry,
)
ram_energy_gauge = Gauge(
    "codecarbon_ram_energy",
    "Energy used per RAM (kWh)",
    ["project_name"],
    registry=registry,
)
energy_consumed_gauge = Gauge(
    "codecarbon_energy_consumed",
    "Sum of cpu_energy, gpu_energy and ram_energy (kW)",
    ["project_name"],
    registry=registry,
)
