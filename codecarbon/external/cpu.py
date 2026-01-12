"""
CPU Power consumption and metrics handling
"""

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import psutil

from codecarbon.core.cpu import IntelPowerGadget, IntelRAPL
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import count_cpus, detect_cpu_model
from codecarbon.external.hardware import BaseHardware
from codecarbon.external.logger import logger

# default W value for a CPU if no model is found in the ref csv
POWER_CONSTANT = 85

#  ratio of TDP estimated to be consumed on average
CONSUMPTION_PERCENTAGE_CONSTANT = 0.5


MODE_CPU_LOAD = "cpu_load"


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
        tracking_pids: Optional[List[int]] = None,
        rapl_include_dram: bool = False,
        rapl_prefer_psys: bool = False,
    ):
        assert tracking_mode in ["machine", "process"]
        self._power_history: List[Power] = []
        self._output_dir = output_dir
        self._mode = mode
        self._model = model
        self._tdp = tdp
        self._is_generic_tdp = False
        self._tracking_mode = tracking_mode
        self._tracking_pids = tracking_pids
        self._cpu_count = count_cpus()

        if self._mode == "intel_power_gadget":
            self._intel_interface = IntelPowerGadget(self._output_dir)
        elif self._mode == "intel_rapl":
            self._intel_interface = IntelRAPL(
                rapl_dir=rapl_dir,
                rapl_include_dram=rapl_include_dram,
                rapl_prefer_psys=rapl_prefer_psys,
            )

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

    def get_cpu_load(self) -> float:
        """
        Get CPU load percentage
        :return: CPU load in percentage
        """
        if self._tracking_mode == "machine":
            cpu_load = psutil.cpu_percent(interval=0.5, percpu=False)
            logger.debug(f"Total CPU load: {cpu_load:.1f} %")
        elif self._tracking_mode == "process":
            cpu_load = 0

            for pid in self._tracking_pids:
                if not psutil.pid_exists(pid):
                    # Log a warning and continue
                    logger.warning(f"Process with pid {pid} does not exist anymore.")
                    continue
                self._process = psutil.Process(pid)
                cpu_load += self._process.cpu_percent(interval=0.5)

                try:
                    children = self._process.children(recursive=True)
                    for child in children:
                        try:
                            # Use interval=0.0 for children to avoid blocking
                            child_cpu = child.cpu_percent(interval=0.0)
                            logger.debug(f"Child {child.pid} CPU: {child_cpu}")
                            cpu_load += child_cpu
                        except (
                            psutil.NoSuchProcess,
                            psutil.AccessDenied,
                            psutil.ZombieProcess,
                        ):
                            # Child process may have terminated or we don't have access
                            continue
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Main process terminated or access denied
                    pass

            # Normalize by CPU count
            logger.info(f"Total CPU load (all processes): {cpu_load}")
            cpu_load = cpu_load / self._cpu_count
        else:
            raise Exception(f"Unknown tracking_mode {self._tracking_mode}")
        return cpu_load

    def _get_power_from_cpu_load(self):
        """
        When in MODE_CPU_LOAD
        """

        cpu_load = self.get_cpu_load()

        if self._tracking_mode == "machine":
            logger.debug(f"CPU load : {self._tdp=} W and {cpu_load:.1f} %")
            # Cubic relationship with minimum 10% of TDP
            load_factor = 0.1 + 0.9 * ((cpu_load / 100.0) ** 3)
            power = self._tdp * load_factor
            logger.debug(
                f"CPU load {self._tdp} W and {cpu_load:.1f}% {load_factor=} => estimation of {power} W for whole machine."
            )
        elif self._tracking_mode == "process":
            # Normalize by CPU count
            logger.info(f"Total CPU load (all processes): {cpu_load}")
            power = self._tdp * cpu_load / 100
            logger.debug(
                f"CPU load {self._tdp} W and {cpu_load * 100:.1f}% => estimation of {power} W for processes {self._tracking_pids} (including children)."
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

        # Rescale power with correct tracking mode
        # Machine -> 100%
        # Process -> With CPU load
        cpu_load = self.get_cpu_load()
        power = self._tdp * cpu_load / 100
        logger.debug(
            f"Estimated CPU power for processes {self._tracking_pids} (including children): {power} W based on CPU load {cpu_load} % and TDP {self._tdp} W."
        )

        return Power.from_watts(power)

    def _get_energy_from_cpus(self, delay: Time) -> Energy:
        """
        Get CPU energy deltas from RAPL files
        :return: energy in kWh
        """
        all_cpu_details: Dict = self._intel_interface.get_cpu_details(delay)

        delta_energy = 0
        for metric, value in all_cpu_details.items():
            if re.match(r"^Processor Energy Delta_\d", metric):
                delta_energy += value
                logger.debug(f"_get_energy_from_cpus - MATCH {metric} : {value}")

        # Rescale energy with correct tracking mode
        # get_cpu_details should never return total energy
        # Machine -> 100%
        # Process -> With CPU load
        cpu_load = self.get_cpu_load()
        delta_energy = self._tdp * cpu_load / 100
        logger.debug(
            f"Estimated CPU power for processes {self._tracking_pids} (including children): {delta_energy} W based on CPU load {cpu_load} % and TDP {self._tdp} W."
        )

        return Energy.from_energy(delta_energy)

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
        tracking_pids: Optional[List[int]] = None,
        rapl_include_dram: bool = False,
        rapl_prefer_psys: bool = False,
    ) -> "CPU":
        if model is None:
            model = detect_cpu_model()
            if model is None:
                logger.warning("Could not read CPU model.")

        if tdp is None:
            tdp = POWER_CONSTANT
            cpu = cls(
                output_dir=output_dir,
                mode=mode,
                model=model,
                tdp=tdp,
                rapl_include_dram=rapl_include_dram,
                rapl_prefer_psys=rapl_prefer_psys,
            )
            cpu._is_generic_tdp = True
            return cpu

        return cls(
            output_dir=output_dir,
            mode=mode,
            model=model,
            tdp=tdp,
            tracking_mode=tracking_mode,
            tracking_pids=tracking_pids,
            rapl_include_dram=rapl_include_dram,
            rapl_prefer_psys=rapl_prefer_psys,
        )
