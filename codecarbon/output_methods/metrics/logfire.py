from logfire import metric_gauge

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData

duration_gauge = metric_gauge(
    "codecarbon_duration", unit="(s)", description="Duration from last measure"
)
emissions_gauge = metric_gauge(
    "codecarbon_emissions",
    unit="(kg)",
    description="Emissions as CO₂-equivalents CO₂eq",
)
emissions_rate_gauge = metric_gauge(
    "codecarbon_emissions_rate",
    unit="(Kg/s)",
    description="Emissions divided per duration",
)

cpu_power_gauge = metric_gauge(
    "codecarbon_cpu_power", unit="(W)", description="CPU power"
)

gpu_power_gauge = metric_gauge(
    "codecarbon_gpu_power", unit="(W)", description="GPU power"
)

ram_power_gauge = metric_gauge(
    "codecarbon_ram_power", unit="(W)", description="RAM power"
)

cpu_energy_gauge = metric_gauge(
    "codecarbon_cpu_energy", unit="(kWh)", description="Energy used per CPU"
)

gpu_energy_gauge = metric_gauge(
    "codecarbon_gpu_energy", unit="(kWh)", description="Energy used per GPU"
)

ram_energy_gauge = metric_gauge(
    "codecarbon_ram_energy", unit="(kWh)", description="Energy used per RAM"
)

energy_consumed_gauge = metric_gauge(
    "codecarbon_ram_energy",
    unit="(kW)",
    description="Sum of cpu_energy, gpu_energy and ram_energy",
)


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
