from dataclasses import dataclass

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger


@dataclass
class RAPLFile:
    name: str
    path: str
    energy_reading: Energy = Energy(0)  # kWh
    energy_delta: Energy = Energy(0)  # kWh
    power: Power = Power(0)
    last_energy = 0

    def __post_init__(self):
        self.last_energy = self._get_value()

    def _get_value(self) -> Energy:
        """
        Reads the value in the file at the path
        """
        with open(self.path, "r") as f:
            micro_joules = float(f.read())

            e = Energy.from_ujoules(micro_joules)
            return e

    def start(self) -> None:
        self.energy_reading = self._get_value()
        self.last_energy = self._get_value()
        return

    def delta(self, duration: Time) -> None:
        """
        Compute the energy used since last call.
        """
        energy = self._get_value()
        if self.last_energy > energy:
            logger.error(
                f"In RAPLFile : Current energy value ({energy}) is lower than previous value ({self.last_energy}) ! Source file : {self.path}"
            )
            self.power = Power(0)
            self.energy_delta = Energy(0)
            return
        else:
            self.power = self.power.from_energies_and_delay(
                energy, self.last_energy, duration
            )
            self.energy_delta = energy - self.last_energy
            self.last_energy = energy

            return
