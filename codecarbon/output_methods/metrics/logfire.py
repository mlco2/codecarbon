from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData

_logfire_configured = False
_logfire_metrics: dict | None = None


def clear_logfire_cache() -> None:
    global _logfire_configured, _logfire_metrics
    _logfire_configured = False
    _logfire_metrics = None


def _ensure_logfire_metrics() -> dict:
    global _logfire_configured, _logfire_metrics
    if _logfire_metrics is not None:
        return _logfire_metrics

    try:
        from logfire import configure, metric_counter, metric_gauge
    except ImportError:
        logger.error(
            "Logfire is not installed. Please install it using `pip install logfire`"
        )
        raise

    if not _logfire_configured:
        configure()
        _logfire_configured = True

    _logfire_metrics = {
        "duration": metric_counter(
            "codecarbon_duration", unit="(s)", description="Duration from last measure"
        ),
        "emissions": metric_counter(
            "codecarbon_emissions",
            unit="(kg)",
            description="Emissions as CO₂-equivalents CO₂eq",
        ),
        "energy_consumed": metric_counter(
            "codecarbon_energy_consumed",
            unit="(kW)",
            description="Sum of cpu_energy, gpu_energy and ram_energy",
        ),
        "emissions_rate": metric_gauge(
            "codecarbon_emissions_rate",
            unit="(Kg/s)",
            description="Emissions divided per duration",
        ),
        "cpu_power": metric_gauge(
            "codecarbon_cpu_power", unit="(W)", description="CPU power"
        ),
        "gpu_power": metric_gauge(
            "codecarbon_gpu_power", unit="(W)", description="GPU power"
        ),
        "ram_power": metric_gauge(
            "codecarbon_ram_power", unit="(W)", description="RAM power"
        ),
        "cpu_energy": metric_gauge(
            "codecarbon_cpu_energy", unit="(kWh)", description="Energy used per CPU"
        ),
        "gpu_energy": metric_gauge(
            "codecarbon_gpu_energy", unit="(kWh)", description="Energy used per GPU"
        ),
        "ram_energy": metric_gauge(
            "codecarbon_ram_energy", unit="(kWh)", description="Energy used per RAM"
        ),
    }
    return _logfire_metrics


class LogfireOutput(BaseOutput):
    """
    Send emissions data to logfire
    """

    def __init__(self):
        metrics = _ensure_logfire_metrics()
        self.duration = metrics["duration"]
        self.emissions = metrics["emissions"]
        self.energy_consumed = metrics["energy_consumed"]
        self.emissions_rate = metrics["emissions_rate"]
        self.cpu_power = metrics["cpu_power"]
        self.gpu_power = metrics["gpu_power"]
        self.ram_power = metrics["ram_power"]
        self.cpu_energy = metrics["cpu_energy"]
        self.gpu_energy = metrics["gpu_energy"]
        self.ram_energy = metrics["ram_energy"]

    def out(self, _, delta: EmissionsData):
        try:
            self.duration.add(delta.duration)
            self.emissions.add(delta.emissions)
            self.emissions_rate.set(delta.emissions_rate)
            self.cpu_power.set(delta.cpu_power)
            self.gpu_power.set(delta.gpu_power)
            self.ram_power.set(delta.ram_power)
            self.cpu_energy.set(delta.cpu_energy)
            self.gpu_energy.set(delta.gpu_energy)
            self.ram_energy.set(delta.ram_energy)
            self.energy_consumed.add(delta.energy_consumed)
            logger.debug("Data sent to logfire")
        except Exception as e:
            logger.error(e, exc_info=True)

    def live_out(self, _: EmissionsData, delta: EmissionsData):
        self.out(None, delta)
