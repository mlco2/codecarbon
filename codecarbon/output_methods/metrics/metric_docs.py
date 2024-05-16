"""_summary_
This module contains the documentation for the metrics that are used in the codecarbon package.
Goal is to provide a common place to generate the metrics with the same information.

Example of how to use it:
    ```python
    from codecarbon.output_methods.metrics.metric_docs import duration_doc
    from prometheus_client import Counter

    duration_counter = Counter(duration_doc.name, duration_doc.description, labelnames, registry=registry)
    ```


"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MetricDocumentation:
    name: str
    description: str
    unit: Optional[str] = None


duration_doc = MetricDocumentation(
    "codecarbon_duration",
    description="Duration from last measure (s)",
)
emissions_doc = MetricDocumentation(
    "codecarbon_emissions",
    description="Emissions as CO₂-equivalents [CO₂eq] (kg)",
)
emissions_rate_doc = MetricDocumentation(
    "codecarbon_emissions_rate",
    description="Emissions divided per duration (Kg/s)",
)
cpu_power_doc = MetricDocumentation(
    "codecarbon_cpu_power",
    description="CPU power (W)",
)
gpu_power_doc = MetricDocumentation(
    "codecarbon_gpu_power",
    description="GPU power (W)",
)
ram_power_doc = MetricDocumentation(
    "codecarbon_ram_power",
    description="RAM power (W)",
)
cpu_energy_doc = MetricDocumentation(
    "codecarbon_cpu_energy",
    description="Energy used per CPU (kWh)",
)
gpu_energy_doc = MetricDocumentation(
    "codecarbon_gpu_energy",
    description="Energy used per GPU (kWh)",
)
ram_energy_doc = MetricDocumentation(
    "codecarbon_ram_energy",
    description="Energy used per RAM (kWh)",
)
energy_consumed_doc = MetricDocumentation(
    "codecarbon_energy_consumed",
    description="Sum of cpu_energy, gpu_energy and ram_energy (kW)",
)
