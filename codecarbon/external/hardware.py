"""
Encapsulates external dependencies to retrieve hardware metadata
"""

import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import psutil

from codecarbon.core.cpu import IntelPowerGadget, IntelRAPL
from codecarbon.core.gpu import AllGPUDevices
from codecarbon.core.powermetrics import ApplePowermetrics
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import count_cpus, detect_cpu_model
from codecarbon.external.logger import logger

# default W value for a CPU if no model is found in the ref csv
POWER_CONSTANT = 85

#  ratio of TDP estimated to be consumed on average
CONSUMPTION_PERCENTAGE_CONSTANT = 0.5

B_TO_GB = 1024 * 1024 * 1024

MODE_CPU_LOAD = "cpu_load"


@dataclass
class BaseHardware(ABC):
    @abstractmethod
    def total_power(self) -> Power:
        pass

    def description(self) -> str:
        return repr(self)

    def measure_power_and_energy(self, last_duration: float) -> Tuple[Power, Energy]:
        """
        Base implementation: we get the power from the
        hardware and convert it to energy.
        """
        power = self.total_power()
        energy = Energy.from_power_and_time(
            power=power, time=Time.from_seconds(last_duration)
        )
        return power, energy

    def start(self) -> None:  # noqa B027
        pass


@dataclass
class GPU(BaseHardware):
    gpu_ids: Optional[List]

    def __repr__(self) -> str:
        return super().__repr__() + " ({})".format(
            ", ".join([d["name"] for d in self.devices.get_gpu_details()])
        )

    def __post_init__(self):
        self.devices = AllGPUDevices()
        self.num_gpus = self.devices.device_count
        self._total_power = Power(
            0  # It will be 0 until we call for the first time measure_power_and_energy
        )

    def measure_power_and_energy(
        self, last_duration: float, gpu_ids: Iterable[int] = None
    ) -> Tuple[Power, Energy]:
        if not gpu_ids:
            gpu_ids = self._get_gpu_ids()
        all_gpu_details: List[Dict] = self.devices.get_delta(
            Time.from_seconds(last_duration)
        )
        # We get the total energy and power of only the ones in gpu_ids
        total_energy = Energy.from_energy(
            sum(
                [
                    gpu_details["delta_energy_consumption"].kWh
                    for idx, gpu_details in enumerate(all_gpu_details)
                    if idx in gpu_ids
                ]
            )
        )
        self._total_power = Power(
            sum(
                [
                    gpu_details["power_usage"].kW
                    for idx, gpu_details in enumerate(all_gpu_details)
                    if idx in gpu_ids
                ]
            )
        )
        return self._total_power, total_energy

    def _get_gpu_ids(self) -> Iterable[int]:
        """
        Get the Ids of the GPUs that we will monitor
        :return: list of ids
        """
        gpu_ids = []
        if self.gpu_ids is not None:
            # Check that the provided GPU ids are valid
            if not set(self.gpu_ids).issubset(set(range(self.num_gpus))):
                logger.warning(
                    f"Unknown GPU ids {gpu_ids}, only {self.num_gpus} GPUs available."
                )
            # Keep only the GPUs that are in the provided list
            for gpu_id in range(self.num_gpus):
                if gpu_id in self.gpu_ids:
                    gpu_ids.append(gpu_id)
                else:
                    logger.info(
                        f"GPU number {gpu_id} will not be monitored, at your request."
                    )
            self.gpu_ids = gpu_ids
        else:
            gpu_ids = set(range(self.num_gpus))
        return gpu_ids

    def total_power(self) -> Power:
        return self._total_power

    def start(self) -> None:
        for d in self.devices.devices:
            d.start()

    @classmethod
    def from_utils(cls, gpu_ids: Optional[List] = None) -> "GPU":
        gpus = cls(gpu_ids=gpu_ids)
        new_gpu_ids = gpus._get_gpu_ids()
        if len(new_gpu_ids) < gpus.num_gpus:
            logger.warning(
                f"You have {gpus.num_gpus} GPUs but we will monitor only {len(gpu_ids)} of them. Check your configuration."
            )
        return cls(gpu_ids=new_gpu_ids)


@dataclass
class CPU(BaseHardware):
    def __init__(
        self,
        output_dir: str,
        mode: str,
        model: str,
        tdp: int,
        rapl_dir: str = "/sys/class/powercap/intel-rapl/subsystem",
        tracking_mode: str = "machine",
    ):
        assert tracking_mode in ["machine", "process"]
        self._power_history: List[Power] = []
        self._output_dir = output_dir
        self._mode = mode
        self._model = model
        self._tdp = tdp
        self._is_generic_tdp = False
        self._tracking_mode = tracking_mode
        self._pid = psutil.Process().pid
        self._cpu_count = count_cpus()
        self._process = psutil.Process(self._pid)

        if self._mode == "intel_power_gadget":
            self._intel_interface = IntelPowerGadget(self._output_dir)
        elif self._mode == "intel_rapl":
            self._intel_interface = IntelRAPL(rapl_dir=rapl_dir)

    def __repr__(self) -> str:
        if self._mode != "constant":
            return f"CPU({' '.join(map(str.capitalize, self._mode.split('_')))})"

        s = f"CPU({self._model} > {self._tdp}W"

        if self._is_generic_tdp:
            s += " [generic]"

        return s + ")"

    @staticmethod
    def _calculate_power_from_cpu_load(tdp, cpu_load, model):
        if "AMD Ryzen Threadripper" in model:
            return CPU._calculate_power_from_cpu_load_treadripper(tdp, cpu_load)
        else:
            # Minimum power consumption is 10% of TDP
            return max(tdp * (cpu_load / 100.0), tdp * 0.1)

    @staticmethod
    def _calculate_power_from_cpu_load_treadripper(tdp, cpu_load):
        load = cpu_load / 100.0

        if load < 0.1:  # Below 10% CPU load
            return tdp * (0.05 * load * 10)
        elif load <= 0.3:  # 10-30% load - linear phase
            return tdp * (0.05 + 1.8 * (load - 0.1))
        elif load <= 0.5:  # 30-50% load - adjusted coefficients
            # Increased base power and adjusted curve
            base_power = 0.45  # Increased from 0.41
            power_range = 0.50  # Increased from 0.44
            factor = ((load - 0.3) / 0.2) ** 1.8  # Reduced power from 2.0 to 1.8
            return tdp * (base_power + power_range * factor)
        else:  # Above 50% - plateau phase
            return tdp * (0.85 + 0.15 * (1 - math.exp(-(load - 0.5) * 5)))

    def _get_power_from_cpu_load(self):
        """
        When in MODE_CPU_LOAD
        """
        if self._tracking_mode == "machine":
            tdp = self._tdp
            cpu_load = psutil.cpu_percent(
                interval=0.5, percpu=False
            )  # Convert to 0-1 range
            logger.debug(f"CPU load : {self._tdp=} W and {cpu_load:.1f} %")
            # Cubic relationship with minimum 10% of TDP
            load_factor = 0.1 + 0.9 * ((cpu_load / 100.0) ** 3)
            power = tdp * load_factor
            logger.debug(
                f"CPU load {self._tdp} W and {cpu_load:.1f}% {load_factor=} => estimation of {power} W for whole machine."
            )
        elif self._tracking_mode == "process":

            cpu_load = self._process.cpu_percent(interval=0.5) / self._cpu_count
            power = self._tdp * cpu_load / 100
            logger.debug(
                f"CPU load {self._tdp} W and {cpu_load * 100:.1f}% => estimation of {power} W for process {self._pid}."
            )
        else:
            raise Exception(f"Unknown tracking_mode {self._tracking_mode}")
        return Power.from_watts(power)

    def _get_power_from_cpus(self) -> Power:
        """
        Get CPU power
        :return: power in kW
        """
        if self._mode == MODE_CPU_LOAD:
            power = self._get_power_from_cpu_load()
            return power
        elif self._mode == "constant":
            power = self._tdp * CONSUMPTION_PERCENTAGE_CONSTANT
            return Power.from_watts(power)
        if self._mode == "intel_rapl":
            # Don't call get_cpu_details to avoid computing energy twice and losing data.
            all_cpu_details: Dict = self._intel_interface.get_static_cpu_details()
        else:
            all_cpu_details: Dict = self._intel_interface.get_cpu_details()

        power = 0
        for metric, value in all_cpu_details.items():
            # "^Processor Power_\d+\(Watt\)$" for Intel Power Gadget
            if re.match(r"^Processor Power", metric):
                power += value
                logger.debug(f"_get_power_from_cpus - MATCH {metric} : {value}")
            else:
                logger.debug(f"_get_power_from_cpus - DONT MATCH {metric} : {value}")
        return Power.from_watts(power)

    def _get_energy_from_cpus(self, delay: Time) -> Energy:
        """
        Get CPU energy deltas from RAPL files
        :return: energy in kWh
        """
        all_cpu_details: Dict = self._intel_interface.get_cpu_details(delay)

        energy = 0
        for metric, value in all_cpu_details.items():
            if re.match(r"^Processor Energy Delta_\d", metric):
                energy += value
                # logger.debug(f"_get_energy_from_cpus - MATCH {metric} : {value}")
        return Energy.from_energy(energy)

    def total_power(self) -> Power:
        self._power_history.append(self._get_power_from_cpus())
        if len(self._power_history) == 0:
            logger.warning("Power history is empty, returning 0 W")
            return Power.from_watts(0)
        power_history_in_W = [power.W for power in self._power_history]
        cpu_power = sum(power_history_in_W) / len(power_history_in_W)
        self._power_history = []
        return Power.from_watts(cpu_power)

    def measure_power_and_energy(self, last_duration: float) -> Tuple[Power, Energy]:
        if self._mode == "intel_rapl":
            energy = self._get_energy_from_cpus(delay=Time(seconds=last_duration))
            power = self.total_power()
            # Patch AMD Threadripper that count 2x the power
            if "AMD Ryzen Threadripper" in self._model:
                power = power / 2
                energy = energy / 2
            return power, energy
        # If not intel_rapl, we call the parent method from BaseHardware
        # to compute energy from power and time
        return super().measure_power_and_energy(last_duration=last_duration)

    def start(self):
        if self._mode in ["intel_power_gadget", "intel_rapl", "apple_powermetrics"]:
            self._intel_interface.start()
        if self._mode == MODE_CPU_LOAD:
            # The first time this is called it will return a meaningless 0.0 value which you are supposed to ignore.
            _ = self._get_power_from_cpu_load()

    def monitor_power(self):
        cpu_power = self._get_power_from_cpus()
        self._power_history.append(cpu_power)

    def get_model(self):
        return self._model

    @classmethod
    def from_utils(
        cls,
        output_dir: str,
        mode: str,
        model: Optional[str] = None,
        tdp: Optional[int] = None,
        tracking_mode: str = "machine",
    ) -> "CPU":
        if model is None:
            model = detect_cpu_model()
            if model is None:
                logger.warning("Could not read CPU model.")

        if tdp is None:
            tdp = POWER_CONSTANT
            cpu = cls(output_dir=output_dir, mode=mode, model=model, tdp=tdp)
            cpu._is_generic_tdp = True
            return cpu

        return cls(
            output_dir=output_dir,
            mode=mode,
            model=model,
            tdp=tdp,
            tracking_mode=tracking_mode,
        )


@dataclass
class AppleSiliconChip(BaseHardware):
    def __init__(
        self,
        output_dir: str,
        model: str,
        chip_part: str = "CPU",
    ):
        self._output_dir = output_dir
        self._model = model
        self._interface = ApplePowermetrics(self._output_dir)
        self.chip_part = chip_part

    def __repr__(self) -> str:
        return f"AppleSiliconChip ({self._model} > {self.chip_part})"

    def _get_power(self) -> Power:
        """
        Get Chip part power
        Args:
            chip_part (str): Chip part to get power from (CPU, GPU)
        :return: power in kW
        """

        all_details: Dict = self._interface.get_details()

        power = 0
        for metric, value in all_details.items():
            if re.match(rf"^{self.chip_part} Power", metric):
                power += value
                logger.debug(f"_get_power_from_cpus - MATCH {metric} : {value}")

            else:
                logger.debug(f"_get_power_from_cpus - DONT MATCH {metric} : {value}")
        return Power.from_watts(power)

    def _get_energy(self, delay: Time) -> Energy:
        """
        Get Chip part energy deltas
        Args:
            chip_part (str): Chip part to get power from (Processor, GPU, etc.)
        :return: energy in kWh
        """
        all_details: Dict = self._interface.get_details(delay)

        energy = 0
        for metric, value in all_details.items():
            if re.match(rf"^{self.chip_part} Energy Delta_\d", metric):
                energy += value
        return Energy.from_energy(energy)

    def total_power(self) -> Power:
        return self._get_power()

    def start(self):
        self._interface.start()

    def get_model(self):
        return self._model

    @classmethod
    def from_utils(
        cls, output_dir: str, model: Optional[str] = None, chip_part: str = "Processor"
    ) -> "AppleSiliconChip":
        if model is None:
            model = detect_cpu_model()
            if model is None:
                logger.warning("Could not read AppleSiliconChip model.")

        return cls(output_dir=output_dir, model=model, chip_part=chip_part)
