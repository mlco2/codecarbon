from dataclasses import dataclass

from codecarbon.core.units import Energy, Time


@dataclass
class RAPLFile:
    name: str
    path: str
    energy_reading: float
    power_measurement: float

    def _get_value(self) -> float:
        """
        Reads the value in the file at the path
        """
        with open(self.path, "r") as f:
            return Energy.from_ujoules(float(f.read()))

    def start(self):
        self.energy_reading = self._get_value()
        return

    def end(self, delay):
        self.power_measurement = (
            abs(self._get_value() - self.energy_reading)
            / Time.from_seconds(delay).hours
        )
        return
