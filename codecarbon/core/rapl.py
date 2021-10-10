from dataclasses import dataclass

from codecarbon.core.units import Energy


@dataclass
class RAPLFile:
    name: str
    path: str
    energy_reading: Energy = Energy(0)  # kWh
    energy_delta: Energy = Energy(0)  # kWh

    def _get_value(self) -> float:
        """
        Reads the value in the file at the path
        """
        with open(self.path, "r") as f:
            micro_joules = float(f.read())
            return Energy.from_ujoules(micro_joules)

    def start(self) -> None:
        self.energy_reading = self._get_value()
        return

    def end(self) -> None:
        self.energy_delta = self.energy_reading - self._get_value()
        return
