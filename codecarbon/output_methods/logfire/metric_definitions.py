from logfire import metric_gauge

duration_gauge = metric_gauge(
    "codecarbon_duration",
    description="Duration from last measure (s)",
)
emissions_gauge = metric_gauge(
    "codecarbon_emissions",
    description="Emissions as CO₂-equivalents [CO₂eq] (kg)",
)
emissions_rate_gauge = metric_gauge(
    "codecarbon_emissions_rate",
    description="Emissions divided per duration (Kg/s)",
)
cpu_power_gauge = metric_gauge(
    "codecarbon_cpu_power",
    description="CPU power (W)",
)
gpu_power_gauge = metric_gauge(
    "codecarbon_gpu_power",
    description="GPU power (W)",
)
ram_power_gauge = metric_gauge(
    "codecarbon_ram_power",
    description="RAM power (W)",
)
cpu_energy_gauge = metric_gauge(
    "codecarbon_cpu_energy",
    description="Energy used per CPU (kWh)",
)
gpu_energy_gauge = metric_gauge(
    "codecarbon_gpu_energy",
    description="Energy used per GPU (kWh)",
)
ram_energy_gauge = metric_gauge(
    "codecarbon_ram_energy",
    description="Energy used per RAM (kWh)",
)
energy_consumed_gauge = metric_gauge(
    "codecarbon_energy_consumed",
    description="Sum of cpu_energy, gpu_energy and ram_energy (kW)",
)
