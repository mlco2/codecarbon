from dataclasses import dataclass, field
from typing import Any, Dict

from codecarbon.core.units import Energy, Power, Time


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
    # Last energy reading in kWh
    last_energy: Energy = field(default_factory=lambda: Energy(0))

    def start(self) -> None:
        self.last_energy = self._get_energy_kwh()

    def __post_init__(self) -> None:
        self.last_energy = self._get_energy_kwh()
        self._init_static_details()

    def _get_energy_kwh(self) -> Energy:
        total_energy_consumption = self._get_total_energy_consumption()
        if total_energy_consumption is None:
            return self.last_energy
        return Energy.from_millijoules(total_energy_consumption)

    def delta(self, duration: Time) -> dict:
        """
        Compute the energy/power used since last call.
        """
        new_last_energy = energy = self._get_energy_kwh()
        self.power = self.power.from_energies_and_delay(
            energy, self.last_energy, duration
        )
        self.energy_delta = energy - self.last_energy
        self.last_energy = new_last_energy
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

    def _to_utf8(self, str_or_bytes) -> Any:
        if hasattr(str_or_bytes, "decode"):
            return str_or_bytes.decode("utf-8", errors="replace")

        return str_or_bytes

    def emit_selection_warning(self) -> None:
        return None
