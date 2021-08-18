from dataclasses import dataclass

from codecarbon.core.units import Energy, Power, Time


@dataclass
class RAPLFile:
    name: str
    path: str
    energy_reading: Energy = Energy(0)
    power_measurement: float = 0  # kW

    def _get_value(self) -> float:
        """
        Reads the value in the file at the path
        """
        with open(self.path, "r") as f:
            micro_joules = float(f.read())
            return Energy.from_ujoules(micro_joules)

    def start(self):
        self.energy_reading = self._get_value()
        return

    def end(self, delay: int) -> None:
        """
        Args:
            delay (int): energy measurement delay in seconds
        """
        self.power_measurement = Power.from_energies_and_delay(
            self.energy_reading, self._get_value(), Time.from_seconds(delay)
        ).kW
        return
