from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger


@dataclass
class GPUDevice:
    """
    Represents a GPU device with associated energy and power metrics.

    Attributes:
        handle (any): An identifier for the GPU device.
        gpu_index (int): The index of the GPU device in the system.
        energy_delta (Energy): The amount of energy consumed by the GPU device
            since the last measurement, expressed in kilowatt-hours (kWh).
            Defaults to an initial value of 0 kWh.
        power (Power): The current power consumption of the GPU device,
            measured in watts (W). Defaults to an initial value of 0 W.
        last_energy (Energy): The last recorded energy reading for the GPU
            device, expressed in kilowatt-hours (kWh). This is used to
            calculate `energy_delta`. Defaults to an initial value of 0 kWh.
    """

    handle: any
    gpu_index: int
    # Power based on reading
    power: Power = field(default_factory=lambda: Power(0))
    # Energy consumed in kWh
    energy_delta: Energy = field(default_factory=lambda: Energy(0))
    # Last good energy counter reading in kWh, None if the device has no
    # energy counter
    last_energy: Optional[Energy] = field(default_factory=lambda: Energy(0))

    # Plain class attributes (not dataclass fields) so that instances built
    # without __init__ (e.g. ``__new__`` in tests) still have sane defaults.
    # True while delta() integrates power instead of reading the counter.
    _use_power_fallback = False
    _warned_no_counter = False
    _warned_power_failure = False
    _warned_zero_power = False
    # Energy reported by the power fallback since ``last_energy`` was read,
    # subtracted once the counter comes back so nothing is counted twice.
    _fallback_energy_since_counter = Energy(0)

    def start(self) -> None:
        self.last_energy = self._get_energy_kwh()
        self._fallback_energy_since_counter = Energy(0)
        self._power_samples = []

    def __post_init__(self) -> None:
        # Static details first: subclasses set flags there (e.g. AMD dual-GCD)
        # that the energy read depends on.
        self._init_static_details()
        self.last_energy = self._get_energy_kwh()
        self._use_power_fallback = self.last_energy is None

    def _get_energy_kwh(self) -> Optional[Energy]:
        total_energy_consumption = self._get_total_energy_consumption()
        if total_energy_consumption is None:
            return None
        return Energy.from_millijoules(total_energy_consumption)

    def _read_power_watts(self) -> Optional[float]:
        try:
            watts = float(self._get_power_usage())
        except Exception:
            if not self._warned_power_failure:
                self._warned_power_failure = True
                logger.warning(
                    f"Failed to retrieve power usage of GPU {self.gpu_index}, "
                    "its energy will be reported as 0 while this persists.",
                    exc_info=True,
                )
            else:
                logger.debug(
                    f"Failed to retrieve power usage of GPU {self.gpu_index}",
                    exc_info=True,
                )
            return None
        self._warned_power_failure = False
        return watts

    def sample_power(self) -> None:
        """
        Record an instantaneous power reading, called every second by the
        tracker. Only does work while the energy counter is unavailable, so
        that the power fallback averages over the whole interval instead of
        relying on a single reading taken at its end.
        """
        if not self._use_power_fallback:
            return
        watts = self._read_power_watts()
        if watts is not None:
            if getattr(self, "_power_samples", None) is None:
                self._power_samples = []
            self._power_samples.append(watts)

    def _delta_from_power(self, duration: Time) -> None:
        # Swap the list rather than clearing it: sample_power() runs in
        # another thread.
        samples = getattr(self, "_power_samples", None) or []
        self._power_samples = []
        if not samples:
            watts = self._read_power_watts()
            samples = [watts] if watts is not None else []
        watts = sum(samples) / len(samples) if samples else 0.0
        if samples and watts == 0 and not self._warned_zero_power:
            self._warned_zero_power = True
            logger.warning(
                f"GPU {self.gpu_index} reports 0 W power usage and has no usable "
                "energy counter, its energy consumption will be under-reported."
            )
        self.power = Power.from_watts(watts)
        self.energy_delta = Energy.from_power_and_time(power=self.power, time=duration)

    def _fall_back_to_power(self, duration: Time) -> None:
        self._use_power_fallback = True
        self._delta_from_power(duration)
        self._fallback_energy_since_counter += self.energy_delta

    def delta(self, duration: Time) -> dict:
        """
        Compute the energy/power used since last call.
        """
        energy = self._get_energy_kwh()
        if energy is None:
            if self.last_energy is None:
                if not self._warned_no_counter:
                    self._warned_no_counter = True
                    logger.warning(
                        f"GPU {self.gpu_index} does not provide a total energy "
                        "consumption counter, falling back to averaging its "
                        "power usage. Measurements will be less accurate."
                    )
            elif not self._use_power_fallback:
                logger.warning(
                    f"Failed to read the energy counter of GPU {self.gpu_index}, "
                    "averaging its power usage until the counter is available again."
                )
            # Keep the last good counter reading, so the energy consumed during
            # the outage is reconciled once the counter comes back.
            self._fall_back_to_power(duration)
        elif self.last_energy is None:
            # Counter appeared after starting without one: no baseline yet.
            self._fall_back_to_power(duration)
            self.last_energy = energy
            self._fallback_energy_since_counter = Energy(0)
        elif energy.kWh < self.last_energy.kWh:
            logger.warning(
                f"Energy counter of GPU {self.gpu_index} went backwards "
                "(driver reload or counter reset), using its power usage "
                "for this measurement."
            )
            self._fall_back_to_power(duration)
            self.last_energy = energy
            self._fallback_energy_since_counter = Energy(0)
        else:
            if self._use_power_fallback:
                logger.info(
                    f"Energy counter of GPU {self.gpu_index} is available again."
                )
                self._use_power_fallback = False
                self._power_samples = []
            # The counter delta also covers any fallback intervals since the
            # last good reading: remove what those intervals already reported.
            counter_delta = energy.kWh - self.last_energy.kWh
            fallback = self._fallback_energy_since_counter.kWh
            self.energy_delta = Energy(max(counter_delta - fallback, 0.0))
            self.power = Power.from_energy_delta_and_delay(self.energy_delta, duration)
            self.last_energy = energy
            self._fallback_energy_since_counter = Energy(0)
        return {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "gpu_index": self.gpu_index,
            "delta_energy_consumption": self.energy_delta,
            "power_usage": self.power,
        }

    def get_static_details(self) -> Dict[str, Any]:
        return {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "total_memory": self._total_memory,
            "power_limit": self._power_limit,
            "gpu_index": self.gpu_index,
        }

    def _init_static_details(self) -> None:
        self._gpu_name = self._get_gpu_name()
        self._uuid = self._get_uuid()
        self._power_limit = self._get_power_limit()
        # Get the memory
        memory = self._get_memory_info()
        self._total_memory = memory.total

    def get_gpu_details(self) -> Dict[str, Any]:
        # Memory
        memory = self._get_memory_info()

        device_details = {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "gpu_index": self.gpu_index,
            "free_memory": memory.free,
            "total_memory": memory.total,
            "used_memory": memory.used,
            "temperature": self._get_temperature(),
            "power_usage": self._get_power_usage(),
            "power_limit": self._power_limit,
            "total_energy_consumption": self._get_total_energy_consumption(),
            "gpu_utilization": self._get_gpu_utilization(),
            "compute_mode": self._get_compute_mode(),
            "compute_processes": self._get_compute_processes(),
            "graphics_processes": self._get_graphics_processes(),
        }
        return device_details

    def get_gpu_utilization_lightweight(self) -> Dict[str, Any]:
        """
        Lightweight alternative to :meth:`get_gpu_details` for the hot path
        (``_monitor_power`` which runs every 1s).

        Only queries the GPU utilization — avoids heavyweight calls like
        memory info, temperature, compute mode, and process lists which are
        not consumed by the tracker's monitoring loop.
        """
        return {
            "gpu_index": self.gpu_index,
            "gpu_utilization": self._get_gpu_utilization(),
        }

    def _to_utf8(self, str_or_bytes) -> Any:
        if hasattr(str_or_bytes, "decode"):
            return str_or_bytes.decode("utf-8", errors="replace")

        return str_or_bytes

    def emit_selection_warning(self) -> None:
        """Hook for backend-specific warnings when a GPU is explicitly selected.

        Backends that need to emit warnings for selected devices should override
        this method. The default implementation is intentionally a no-op.
        """
        return None
