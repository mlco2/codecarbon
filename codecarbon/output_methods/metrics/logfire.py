from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData


class LogfireOutput(BaseOutput):
    """
    Send emissions data to logfire
    """

    def __init__(self):
        self.use_emissions_delta = True
        try:
            from logfire import metric_counter, metric_gauge
        except ImportError:
            logger.error(
                "Logfire is not installed. Please install it using `pip install logfire`"
            )
            raise

        # Counters
        self.duration = metric_counter(
            "codecarbon_duration", unit="(s)", description="Duration from last measure"
        )
        self.emissions = metric_counter(
            "codecarbon_emissions",
            unit="(kg)",
            description="Emissions as CO₂-equivalents CO₂eq",
        )
        self.energy_consumed = metric_counter(
            "codecarbon_energy_consumed",
            unit="(kW)",
            description="Sum of cpu_energy, gpu_energy and ram_energy",
        )

        # Gauges
        self.emissions_rate = metric_gauge(
            "codecarbon_emissions_rate",
            unit="(Kg/s)",
            description="Emissions divided per duration",
        )
        self.cpu_power = metric_gauge(
            "codecarbon_cpu_power", unit="(W)", description="CPU power"
        )
        self.gpu_power = metric_gauge(
            "codecarbon_gpu_power", unit="(W)", description="GPU power"
        )
        self.ram_power = metric_gauge(
            "codecarbon_ram_power", unit="(W)", description="RAM power"
        )
        self.cpu_energy = metric_gauge(
            "codecarbon_cpu_energy", unit="(kWh)", description="Energy used per CPU"
        )
        self.gpu_energy = metric_gauge(
            "codecarbon_gpu_energy", unit="(kWh)", description="Energy used per GPU"
        )
        self.ram_energy = metric_gauge(
            "codecarbon_ram_energy", unit="(kWh)", description="Energy used per RAM"
        )

    def out(self, data: EmissionsData):
        try:
            self.duration.add(data.duration)
            self.emissions.add(data.emissions)
            self.emissions_rate.set(data.emissions_rate)
            self.cpu_power.set(data.cpu_power)
            self.gpu_power.set(data.gpu_power)
            self.ram_power.set(data.ram_power)
            self.cpu_energy.set(data.cpu_energy)
            self.gpu_energy.set(data.gpu_energy)
            self.ram_energy.set(data.ram_energy)
            self.energy_consumed.add(data.energy_consumed)
            logger.debug("Data sent to logfire")
        except Exception as e:
            logger.error(e, exc_info=True)
