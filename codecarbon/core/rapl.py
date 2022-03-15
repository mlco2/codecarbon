from dataclasses import dataclass

from numpy import power

from codecarbon.core.units import Energy, Power, Time


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

    def end(self) -> None:
        self.energy_delta = self.energy_reading - self._get_value()
        return

    def delta(self, duration: Time) -> None:
        """
        Compute the energy used since last call.
        """
        energy = self._get_value()
        self.energy_delta = energy - self.last_energy
        self.last_energy = energy
        self.power = power.from_energy_delta_and_delay(energy, duration)
        return
