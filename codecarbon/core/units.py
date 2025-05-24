"""
Provides functionality for unit conversions
"""

from dataclasses import dataclass, field

# from pydantic.dataclasses import dataclass, field


@dataclass
class Time:
    """
    Measured in seconds
    """

    seconds: float
    SECONDS_TO_HOURS = 1 / 3600

    @property
    def hours(self) -> float:
        return self.seconds * Time.SECONDS_TO_HOURS

    @classmethod
    def from_seconds(cls, seconds: float) -> "Time":
        return cls(seconds=seconds)


@dataclass
class EmissionsPerKWh:
    """
    Measured in kg/kWh
    """

    LBS_MWH_TO_KG_KWH = 0.00045359237
    G_KWH_TO_KG_KWH = 0.001

    kgs_per_kWh: float

    @classmethod
    def from_lbs_per_mWh(cls, lbs_per_mWh: float) -> "EmissionsPerKWh":
        return cls(kgs_per_kWh=lbs_per_mWh * EmissionsPerKWh.LBS_MWH_TO_KG_KWH)

    @classmethod
    def from_g_per_kWh(cls, g_per_kWh: float) -> "EmissionsPerKWh":
        return cls(kgs_per_kWh=g_per_kWh * EmissionsPerKWh.G_KWH_TO_KG_KWH)

    @classmethod
    def from_kgs_per_kWh(cls, kgs_per_kWh: float) -> "EmissionsPerKWh":
        return cls(kgs_per_kWh=kgs_per_kWh)


@dataclass(order=True)
class Energy:
    """
    Measured in kWh
    """

    UJOULES_TO_JOULES = 10 ** (-6)
    MILLIJOULES_TO_JOULES = 10 ** (-3)
    JOULES_TO_KWH = 2.77778e-7

    kWh: float = field(compare=True)

    def __post_init__(self):
        self.kWh = float(self.kWh)

    @classmethod
    def from_power_and_time(cls, *, power: "Power", time: "Time") -> "Energy":
        assert isinstance(power.kW, float)
        assert isinstance(time.hours, float)
        energy = power.kW * time.hours
        return cls(kWh=energy)

    @classmethod
    def from_ujoules(cls, energy: float) -> "Energy":
        return cls(kWh=energy * Energy.UJOULES_TO_JOULES * Energy.JOULES_TO_KWH)

    @classmethod
    def from_millijoules(cls, energy: float) -> "Energy":
        return cls(kWh=energy * Energy.MILLIJOULES_TO_JOULES * Energy.JOULES_TO_KWH)

    @classmethod
    def from_energy(cls, kWh: float) -> "Energy":
        return cls(kWh=kWh)

    def __sub__(self, other: "Energy") -> "Energy":
        return Energy(self.kWh - other.kWh)

    def __add__(self, other: "Energy") -> "Energy":
        return Energy(self.kWh + other.kWh)

    def __mul__(self, factor: float) -> "Energy":
        assert isinstance(factor, float)
        assert isinstance(self.kWh, float)
        result = Energy(self.kWh * factor)
        return result

    def __float__(self) -> float:
        return float(self.kWh)

    def __truediv__(self, divisor: float) -> "Energy":
        return Energy(self.kWh / divisor)


@dataclass
class Power:
    """
    Measured in kW
    """

    MILLI_WATTS_TO_WATTS = 0.001
    WATTS_TO_KILO_WATTS = 0.001

    kW: float

    @classmethod
    def from_milli_watts(cls, milli_watts: float) -> "Power":
        return cls(
            kW=milli_watts * Power.MILLI_WATTS_TO_WATTS * Power.WATTS_TO_KILO_WATTS
        )

    @classmethod
    def from_watts(cls, watts: float) -> "Power":
        return cls(kW=watts * Power.WATTS_TO_KILO_WATTS)

    @classmethod
    def from_energies_and_delay(cls, e1: "Energy", e2: "Energy", delay: "Time"):
        """
        P = (E_{t1} - E_{t2}) / delay (=t2-t1)
        kW      kWh       kWh     h

        Args:
            e1 (Energy): First measurement
            e2 (Energy): Second measurement
            delay (Time): Time between measurements

        Returns:
            Power: Resulting Power estimation
        """
        delta_energy = float(abs(e2.kWh - e1.kWh))
        kW = delta_energy / delay.hours if delay.hours != 0.0 else 0.0
        return cls(kW=kW)

    @classmethod
    def from_energy_delta_and_delay(cls, e: "Energy", delay: "Time"):
        return cls.from_energies_and_delay(e, Energy(0), delay)

    @property
    def W(self):
        if not isinstance(self.kW, float):
            return self.kW
        return self.kW * 1000

    def __add__(self, other: "Power") -> "Power":
        return Power(self.kW + other.kW)

    def __mul__(self, factor: float) -> "Power":
        return Power(self.kW * factor)

    def __truediv__(self, divisor: float) -> "Power":
        return Power(self.kW / divisor)

    def __floordiv__(self, divisor: float) -> "Power":
        return Power(self.kW // divisor)
