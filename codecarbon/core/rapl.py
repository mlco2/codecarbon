from dataclasses import dataclass, field
from typing import Optional

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger

# Maximum relative difference between two cumulative energy counters for them
# to be considered two views of the same hardware counter. Multi-die CPUs
# (e.g. AMD Ryzen Threadripper / EPYC) can expose one package domain per die
# that all mirror the same socket-wide counter, which would multiply the
# reported CPU power by the number of dies.
# See https://github.com/mlco2/codecarbon/issues/1274
MIRRORED_COUNTER_TOLERANCE = 1e-6

# Unlike EMI, which snapshots all the channels of a device atomically, the
# powercap sysfs files are read one after the other: two views of the same
# hardware counter differ by the energy the package accrued between the two
# reads. One joule covers several milliseconds at full load, while staying
# far below what independent packages drift apart by over a measurement
# interval.
SEQUENTIAL_READ_TOLERANCE_KWH = float(Energy.from_ujoules(1_000_000))  # 1 J


def counters_match(first, second, abs_tolerance=0.0) -> bool:
    """Tell whether two cumulative counter values are indistinguishable."""
    return abs(first - second) <= max(
        MIRRORED_COUNTER_TOLERANCE * max(first, second), abs_tolerance
    )


def find_mirrored_counters(counters, abs_tolerance=0.0) -> dict:
    """
    Identify the counters that report the same underlying energy value.

    ``counters`` is an ordered list of ``(key, absolute_energy)`` pairs whose
    energies share a unit. Two independent meters are extremely unlikely to
    hold the very same cumulative count, so equal counters point at duplicated
    ones. A zero counter carries no information and is never flagged.

    Returns a mapping of each duplicating key to the earlier key it mirrors.
    """
    references = []
    mirrored = {}
    for key, energy in counters:
        if energy <= 0:
            continue
        for reference_key, reference in references:
            if counters_match(energy, reference, abs_tolerance):
                mirrored[key] = reference_key
                break
        else:
            references.append((key, energy))
    return mirrored


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
    # Last energy reading in kWh, None if it could not be read
    last_energy: Optional[Energy] = field(default_factory=lambda: Energy(0))
    # Max value energy can hold before it wraps
    max_energy_reading: Energy = field(default_factory=lambda: Energy(0))
    _warned_uncorrectable_wrap: bool = field(default=False, init=False)

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

    def _get_value(self) -> Optional[Energy]:
        """
        Reads the value in the file at the path, or None if it cannot be read.
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
            return None

    def start(self) -> None:
        self.last_energy = self._get_value()

    def _skip_sample(self, new_last_energy: Optional[Energy]) -> None:
        self.energy_delta = Energy(0)
        self.power = Power(0)
        self.last_energy = new_last_energy

    def delta(self, duration: Time) -> None:
        """
        Compute the energy used since last call.
        """
        new_last_energy = energy = self._get_value()
        if energy is None or self.last_energy is None:
            # no baseline to compute a delta from: re-baseline silently
            self._skip_sample(new_last_energy)
            return
        if self.last_energy > energy:
            logger.debug(
                f"In RAPLFile : Current energy value ({energy}) is lower than previous value ({self.last_energy}). Assuming wrap-around! Source file : {self.path}"
            )
            energy = energy + self.max_energy_reading
        if self.last_energy > energy:
            # still backwards after correction: skip rather than report a negative delta
            if not self._warned_uncorrectable_wrap:
                self._warned_uncorrectable_wrap = True
                logger.warning(
                    "In RAPLFile : counter went backwards and cannot be corrected for %s; skipping this sample (warned once).",
                    self.path,
                )
            self._skip_sample(new_last_energy)
            return
        self.power = self.power.from_energies_and_delay(
            energy, self.last_energy, duration
        )
        self.energy_delta = energy - self.last_energy
        self.last_energy = new_last_energy
