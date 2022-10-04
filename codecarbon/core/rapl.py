from dataclasses import dataclass

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger


@dataclass
class RAPLFile:
    name: str  # RAPL device being measured
    path: str  # Path to file containing RAPL reading
    max_path: str  # Path to corresponding file containing maximum possible RAPL reading
    energy_delta: Energy = Energy(0)  # Energy consumed in kWh
    power: Power = Power(0)  # Power based on reading
    last_energy: Energy = Energy(0)  # Last energy reading in kWh
    max_energy_reading: Energy = Energy(0)  # Max value energy can hold before it wraps

    def __post_init__(self):
        self.last_energy = self._get_value()
        with open(self.max_path, "r") as f:
            max_micro_joules = float(f.read())

            self.max_energy_reading = Energy.from_ujoules(max_micro_joules)

    def _get_value(self) -> Energy:
        """
        Reads the value in the file at the path
        """
        with open(self.path, "r") as f:
            micro_joules = float(f.read())

            e = Energy.from_ujoules(micro_joules)
            return e

    def start(self) -> None:
        self.last_energy = self._get_value()
        return

    def delta(self, duration: Time) -> None:
        """
        Compute the energy used since last call.
        """
        new_last_energy = energy = self._get_value()
        if self.last_energy > energy:
            logger.debug(
                f"In RAPLFile : Current energy value ({energy}) is lower than previous value ({self.last_energy}). Assuming wrap-around! Source file : {self.path}"
            )
            energy = energy + self.max_energy_reading
        self.power = self.power.from_energies_and_delay(
            energy, self.last_energy, duration
        )
        self.energy_delta = energy - self.last_energy
        self.last_energy = new_last_energy

        return
