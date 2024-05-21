from logfire import metric_gauge

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

duration_gauge = metric_gauge(
    "codecarbon_duration",
    unit="(s)",
    description="Duration from last measure"
)
emissions_gauge = metric_gauge(
    "codecarbon_emissions",
    unit="(kg)",
    description="Emissions as CO₂-equivalents CO₂eq"
)
emissions_rate_gauge = metric_gauge(
    "codecarbon_emissions_rate",
    unit="(Kg/s)",
    description="Emissions divided per duration"
)

cpu_power_gauge = metric_gauge(
    "codecarbon_cpu_power",
    unit="(W)",
    description="CPU power"
)

gpu_power_gauge = metric_gauge(
    "codecarbon_gpu_power",
    unit="(W)",
    description="GPU power"
)

ram_power_gauge = metric_gauge(
    "codecarbon_ram_power",
    unit="(W)",
    description="RAM power"
)

cpu_energy_gauge = metric_gauge(
    "codecarbon_cpu_energy",
    unit="(kWh)",
    description="Energy used per CPU"
)

gpu_energy_gauge = metric_gauge(
    "codecarbon_gpu_energy",
    unit="(kWh)",
    description="Energy used per GPU"
)

ram_energy_gauge = metric_gauge(
    "codecarbon_ram_energy",
    unit="(kWh)",
    description="Energy used per RAM"
)

energy_consumed_gauge = metric_gauge(
    "codecarbon_ram_energy",
    unit="(kW)",
    description="Sum of cpu_energy, gpu_energy and ram_energy"
)
