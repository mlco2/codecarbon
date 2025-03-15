"""
Encapsulates external dependencies to retrieve hardware metadata
"""

import math
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import psutil

from codecarbon.core.cpu import IntelPowerGadget, IntelRAPL
from codecarbon.core.gpu import AllGPUDevices
from codecarbon.core.powermetrics import ApplePowermetrics
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import SLURM_JOB_ID, count_cpus, detect_cpu_model
from codecarbon.external.logger import logger

# default W value for a CPU if no model is found in the ref csv
POWER_CONSTANT = 85

#  ratio of TDP estimated to be consumed on average
CONSUMPTION_PERCENTAGE_CONSTANT = 0.5

B_TO_GB = 1024 * 1024 * 1024

MODE_CPU_LOAD = "cpu_load"

RAM_SLOT_POWER_X86 = 4  # Watts


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
            return tdp * (cpu_load / 100.0)

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
            cpu_load = psutil.cpu_percent(interval=0.5)
            power = self._calculate_power_from_cpu_load(tdp, cpu_load, self._model)
            logger.debug(
                f"A TDP of {self._tdp} W and a CPU load of {cpu_load:.1f}% give an estimation of {power:1f} W for whole machine."
            )
        elif self._tracking_mode == "process":
            cpu_load = self._process.cpu_percent(interval=0.5) / self._cpu_count
            power = self._calculate_power_from_cpu_load(
                self._tdp, cpu_load, self._model
            )
            logger.debug(
                f"A TDP of {self._tdp} W and a CPU load of {cpu_load:.1f}% give an estimation of {power:1f} W for process {self._pid}."
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
class RAM(BaseHardware):
    """
    Before V3 heuristic:
    # 3 watts of power for every 8GB of DDR3 or DDR4 memory
    # https://www.crucial.com/support/articles-faq-memory/how-much-power-does-memory-use

    In V3, we need to improve the accuracy of the RAM power estimation.
    Because the power consumption of RAM is not linear with the amount of memory used,
    for example, in servers you could have thousands of GB of RAM but the power
    consumption would not be proportional to the amount of memory used, but to the number
    of memory modules used.
    But there is no way to know the memory modules used in the system, without admin rights.
    So we need to build a heuristic that is more accurate than the previous one.
    For example keep a minimum of 2 modules. Execept for ARM CPU like rapsberry pi where we will consider a 3W constant.
    Then consider the max RAM per module is 128GB and that RAM module only exist in power of 2 (2, 4, 8, 16, 32, 64, 128).
    So we can estimate the power consumption of the RAM by the number of modules used.

    1. **ARM CPU Detection**:
    - Added a `_detect_arm_cpu` method that checks if the system is using an ARM architecture
    - For ARM CPUs (like Raspberry Pi), a constant 3W will be used as the minimum power

    2. **DIMM Count Estimation**:
    - Created a `_estimate_dimm_count` method that intelligently estimates how many memory modules might be present based on total RAM size
    - Takes into account that servers typically have more and larger DIMMs
    - Assumes DIMM sizes follow powers of 2 (4GB, 8GB, 16GB, 32GB, 64GB, 128GB) as specified

    3. **Scaling Power Model**:
    - Base power per DIMM is 2.5W for x86 systems and 1.5W for ARM systems
    - For standard systems (up to 4 DIMMs): linear scaling at full power per DIMM
    - For medium systems (5-8 DIMMs): decreasing efficiency (90% power per additional DIMM)
    - For large systems (9-16 DIMMs): further reduced efficiency (80% power per additional DIMM)
    - For very large systems (17+ DIMMs): highest efficiency (70% power per additional DIMM)

    4. **Minimum Power Guarantees**:
    - Ensures at least 5W for x86 systems (assuming 2 DIMMs at minimum)
    - Ensures at least 3W for ARM systems as requested

    ### Example Power Estimates:

    - **Small laptop (8GB RAM)**: ~5W (2 DIMMs at 2.5W each)
    - **Desktop (32GB RAM)**: ~10W (4 DIMMs at 2.5W each)
    - **Small server (128GB RAM)**: ~18.6W (8 DIMMs with efficiency scaling)
    - **Large server (1TB RAM)**: ~44W (using 16x64GB DIMMs with high efficiency scaling)

    This approach significantly improves the accuracy for large servers by recognizing that RAM power consumption doesn't scale linearly with capacity, but rather with the number of physical modules. Since we don't have direct access to the actual DIMM configuration, this heuristic provides a more reasonable estimate than the previous linear model.

    The model also includes detailed debug logging that will show the estimated power for given memory sizes, helping with validation and fine-tuning in the future.
    """

    memory_size = None
    is_arm_cpu = False

    def __init__(
        self,
        pid: int = psutil.Process().pid,
        children: bool = True,
        tracking_mode: str = "machine",
    ):
        """
        Instantiate a RAM object from a reference pid. If none is provided, will use the
        current process's. The `pid` is used to find children processes if `children`
        is True.

        Args:
            pid (int, optional): Process id (with respect to which we'll look for
                                 children). Defaults to psutil.Process().pid.
            children (int, optional): Look for children of the process when computing
                                      total RAM used. Defaults to True.
        """
        self._pid = pid
        self._children = children
        self._tracking_mode = tracking_mode
        # Check if using ARM architecture
        self.is_arm_cpu = self._detect_arm_cpu()

    def _detect_arm_cpu(self) -> bool:
        """
        Detect if the CPU is ARM-based
        """
        try:
            # Try to detect ARM architecture using platform module
            import platform

            machine = platform.machine().lower()
            return any(arm in machine for arm in ["arm", "aarch"])
        except Exception:
            # Default to False if detection fails
            return False

    def _estimate_dimm_count(self, total_gb: float) -> int:
        """
        Estimate the number of memory DIMMs based on total memory size
        using heuristic rules.

        Args:
            total_gb: Total RAM in GB

        Returns:
            int: Estimated number of memory DIMMs
        """
        # Typical DIMM sizes in GB
        dimm_sizes = [4, 8, 16, 32, 64, 128]

        # For very small amounts of RAM (e.g. embedded systems)
        if total_gb <= 2:
            return 1

        # For standard desktop/laptop (4-32GB)
        if total_gb <= 32:
            # Estimate based on likely configurations (2-4 DIMMs)
            return max(2, min(4, int(total_gb / 8) + 1))

        # For workstations and small servers (32-128GB)
        if total_gb <= 128:
            # Likely 4-8 DIMMs
            return max(4, min(8, int(total_gb / 16) + 1))

        # For larger servers (>128GB)
        # Estimate using larger DIMM sizes and more slots
        # Most servers have 8-32 DIMM slots
        # Try to find the best fit with common DIMM sizes
        dimm_count = 8  # Minimum for a large server

        # Find the largest common DIMM size that fits
        for dimm_size in sorted(dimm_sizes, reverse=True):
            if dimm_size <= total_gb / 8:  # Assume at least 8 DIMMs
                # Calculate how many DIMMs of this size would be needed
                dimm_count = math.ceil(total_gb / dimm_size)
                # Cap at 32 DIMMs (very large server)
                dimm_count = min(dimm_count, 32)
                break

        return dimm_count

    def _calculate_ram_power(self, memory_gb: float) -> float:
        """
        Calculate RAM power consumption based on the total RAM size using a more
        sophisticated model that better scales with larger memory sizes.

        Args:
            memory_gb: Total RAM in GB

        Returns:
            float: Estimated power consumption in watts
        """
        # Detect how many DIMMs might be present
        dimm_count = self._estimate_dimm_count(memory_gb)

        # Base power consumption per DIMM
        if self.is_arm_cpu:
            # ARM systems typically use lower power memory
            base_power_per_dimm = 1.5  # Watts
            # Minimum 3W for ARM as requested
            min_power = 3.0
        else:
            # x86 systems
            base_power_per_dimm = RAM_SLOT_POWER_X86  # Watts
            # Minimum 5W for x86 as requested (2 sticks at 2.5W)
            min_power = base_power_per_dimm * 2

        # Estimate power based on DIMM count with decreasing marginal power per DIMM as count increases
        if dimm_count <= 4:
            # Small systems: full power per DIMM
            total_power = base_power_per_dimm * dimm_count
        elif dimm_count <= 8:
            # Medium systems: slight efficiency at scale
            total_power = base_power_per_dimm * 4 + base_power_per_dimm * 0.9 * (
                dimm_count - 4
            )
        elif dimm_count <= 16:
            # Larger systems: better efficiency at scale
            total_power = (
                base_power_per_dimm * 4
                + base_power_per_dimm * 0.9 * 4
                + base_power_per_dimm * 0.8 * (dimm_count - 8)
            )
        else:
            # Very large systems: high efficiency at scale
            total_power = (
                base_power_per_dimm * 4
                + base_power_per_dimm * 0.9 * 4
                + base_power_per_dimm * 0.8 * 8
                + base_power_per_dimm * 0.7 * (dimm_count - 16)
            )

        # Apply minimum power constraint
        return max(min_power, total_power)

    def _get_children_memories(self):
        """
        Compute the used RAM by the process's children

        Returns:
            list(int): The list of RAM values
        """
        current_process = psutil.Process(self._pid)
        children = current_process.children(recursive=True)
        return [child.memory_info().rss for child in children]

    def _read_slurm_scontrol(self):
        try:
            logger.debug(
                "SLURM environment detected, running `scontrol show job $SLURM_JOB_ID`..."
            )
            return (
                subprocess.check_output(
                    [f"scontrol show job {SLURM_JOB_ID}"], shell=True
                )
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            return

    def _parse_scontrol_memory_GB(self, mem):
        """
        Parse the memory string (B) returned by scontrol to a float (GB)

        Args:
            mem (str): Memory string (B) as `[amount][unit]` (e.g. `128G`)

        Returns:
            float: Memory (GB)
        """
        nb = int(mem[:-1])
        unit = mem[-1]
        if unit == "T":
            return nb * 1000
        if unit == "G":
            return nb
        if unit == "M":
            return nb / 1000
        if unit == "K":
            return nb / (1000**2)

    def _parse_scontrol(self, scontrol_str):
        mem_matches = re.findall(r"AllocTRES=.*?,mem=(\d+[A-Z])", scontrol_str)
        if len(mem_matches) == 0:
            # Try with TRES, see https://github.com/mlco2/codecarbon/issues/569#issuecomment-2167706145
            mem_matches = re.findall(r"TRES=.*?,mem=(\d+[A-Z])", scontrol_str)
        if len(mem_matches) == 0:
            logger.warning(
                "Could not find mem= after running `scontrol show job $SLURM_JOB_ID` "
                + "to count SLURM-available RAM. Using the machine's total RAM."
            )
            return psutil.virtual_memory().total / B_TO_GB
        if len(mem_matches) > 1:
            logger.warning(
                "Unexpected output after running `scontrol show job $SLURM_JOB_ID` "
                + "to count SLURM-available RAM. Using the machine's total RAM."
            )
            return psutil.virtual_memory().total / B_TO_GB

        return mem_matches[0].replace("mem=", "")

    @property
    def slurm_memory_GB(self):
        """
        Property to compute the SLURM-available RAM in GigaBytes.

        Returns:
            float: Memory allocated to the job (GB)
        """
        # Prevent calling scontrol at each mesure
        if self.memory_size:
            return self.memory_size
        scontrol_str = self._read_slurm_scontrol()
        if scontrol_str is None:
            logger.warning(
                "Error running `scontrol show job $SLURM_JOB_ID` "
                + "to retrieve SLURM-available RAM."
                + "Using the machine's total RAM."
            )
            return psutil.virtual_memory().total / B_TO_GB
        mem = self._parse_scontrol(scontrol_str)
        if isinstance(mem, str):
            mem = self._parse_scontrol_memory_GB(mem)
        self.memory_size = mem
        return mem

    @property
    def process_memory_GB(self):
        """
        Property to compute the process's total memory usage in bytes.

        Returns:
            float: RAM usage (GB)
        """
        children_memories = self._get_children_memories() if self._children else []
        main_memory = psutil.Process(self._pid).memory_info().rss
        memories = children_memories + [main_memory]
        return sum([m for m in memories if m] + [0]) / B_TO_GB

    @property
    def machine_memory_GB(self):
        """
        Property to compute the machine's total memory in bytes.

        Returns:
            float: Total RAM (GB)
        """
        return (
            self.slurm_memory_GB
            if SLURM_JOB_ID
            else psutil.virtual_memory().total / B_TO_GB
        )

    def total_power(self) -> Power:
        """
        Compute the Power (kW) consumed by the current process (and its children if
        `children` was True in __init__)

        Returns:
            Power: kW of power consumption, using a more sophisticated power model
        """
        try:
            memory_GB = (
                self.machine_memory_GB
                if self._tracking_mode == "machine"
                else self.process_memory_GB
            )
            ram_power = Power.from_watts(self._calculate_ram_power(memory_GB))
            logger.debug(
                f"RAM power estimation: {ram_power.W:.2f}W for {memory_GB:.2f}GB"
            )
        except Exception as e:
            logger.warning(f"Could not measure RAM Power ({str(e)})")
            ram_power = Power.from_watts(0)

        return ram_power


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
