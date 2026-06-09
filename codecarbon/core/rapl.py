from dataclasses import dataclass, field

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger


@dataclass
class RAPLFile:
    # RAPL device being measured
    name: str
    # Path to file containing RAPL reading
    path: str
    # Path to corresponding file containing maximum possible RAPL reading
    max_path: str
    # Energy consumed in kWh
    energy_delta: Energy = field(default_factory=lambda: Energy(0))
    # Power based on reading
    power: Power = field(default_factory=lambda: Power(0))
    # Last energy reading in kWh
    last_energy: Energy = field(default_factory=lambda: Energy(0))
    # Max value energy can hold before it wraps
    max_energy_reading: Energy = field(default_factory=lambda: Energy(0))

    def __post_init__(self):
        self.last_energy = self._get_value()
        try:
            with open(self.max_path, "r") as f:
                max_micro_joules = float(f.read())
                self.max_energy_reading = Energy.from_ujoules(max_micro_joules)
        except Exception as e:
            # If we cannot read the max range, log and set to 0 so wrap detection
            # will be effectively disabled for this file.
            if isinstance(e, PermissionError):
                logger.warning(
                    "Unable to read max_energy_range_uj from %s due to permission error: %s",
                    self.max_path,
                    e,
                )
            else:
                logger.debug(
                    "Unable to read max_energy_range_uj from %s: %s",
                    self.max_path,
                    e,
                )
            self.max_energy_reading = Energy.from_ujoules(0)

    def _get_value(self) -> Energy:
        """
        Reads the value in the file at the path
        """
        try:
            with open(self.path, "r") as f:
                micro_joules = float(f.read())
                return Energy.from_ujoules(micro_joules)
        except Exception as e:
            # Be tolerant to transient IO / permission errors while reading energy.
            if isinstance(e, PermissionError):
                logger.warning(
                    "Unable to read RAPL value from %s due to permission error: %s",
                    self.path,
                    e,
                )
            else:
                logger.debug("Unable to read RAPL value from %s: %s", self.path, e)
            return Energy.from_ujoules(0)

    def start(self) -> None:
        self.last_energy = self._get_value()

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
