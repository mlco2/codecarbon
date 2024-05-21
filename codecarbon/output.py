"""
Provides functionality for persistence of data
"""

from codecarbon.output_methods.base_output import BaseOutput  # noqa: F401

# emissions data
from codecarbon.output_methods.emissions_data import (  # noqa: F401
    EmissionsData,
    TaskEmissionsData,
)

# Output to a file
from codecarbon.output_methods.file import FileOutput  # noqa: F401

# Output calling a REST http endpoint
from codecarbon.output_methods.http import CodeCarbonAPIOutput, HTTPOutput  # noqa: F401

# Output to a logger
from codecarbon.output_methods.logger import (  # noqa: F401
    GoogleCloudLoggerOutput,
    LoggerOutput,
)

# output is sent to metrics
from codecarbon.output_methods.metrics.prometheus.prometheus import (  # noqa: F401
    PrometheusOutput,
)

from codecarbon.logfire.metric_definitions import duration_gauge, emissions_gauge, emissions_rate_gauge, \
    gpu_power_gauge, ram_power_gauge, cpu_power_gauge, ram_energy_gauge, gpu_energy_gauge, cpu_energy_gauge

    
class LogfireOutput(BaseOutput):
    """
    Send emissions data to logfire
    """

    def __init__(self):
        self.duration = duration_gauge
        self.emissions = emissions_gauge
        self.emissions_rate = emissions_rate_gauge
        self.cpu_power = cpu_power_gauge
        self.gpu_power = gpu_power_gauge
        self.ram_power = ram_power_gauge
        self.cpu_energy = cpu_energy_gauge
        self.gpu_energy = gpu_energy_gauge
        self.ram_energy = ram_energy_gauge

    def out(self, data: EmissionsData):
        try:
            self.duration.set(data.duration)
            self.emissions.set(data.emissions)
            self.emissions_rate.set(data.emissions_rate)
            self.cpu_power.set(data.cpu_power)
            self.gpu_power.set(data.gpu_power)
            self.ram_power.set(data.ram_power)
            self.cpu_energy.set(data.cpu_energy)
            self.gpu_energy.set(data.gpu_energy)
            self.ram_energy.set(data.ram_energy)
        except Exception as e:
            logger.error(e, exc_info=True)

