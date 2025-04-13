import math
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

import psutil

from codecarbon.core.units import Power
from codecarbon.core.util import SLURM_JOB_ID
from codecarbon.external.hardware import B_TO_GB, BaseHardware
from codecarbon.external.logger import logger

RAM_SLOT_POWER_X86 = 5  # Watts


@dataclass
class RAM(BaseHardware):
    """
    Before V3 heuristic:
    # 3 watts of power for every 8GB of DDR3 or DDR4 memory
    # https://www.crucial.com/support/articles-faq-memory/how-much-power-does-memory-use

    In V3, we need to improve the accuracy of the RAM power estimation.
    Because the power consumption of RAM is not linear with the amount of memory used,

    See https://mlco2.github.io/codecarbon/methodology.html#ram for details on the RAM
    power estimation methodology.

    """

    memory_size = None
    is_arm_cpu = False

    def __init__(
        self,
        pid: int = psutil.Process().pid,
        children: bool = True,
        tracking_mode: str = "machine",
        force_ram_power: Optional[int] = None,
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
            tracking_mode (str, optional): Whether to track "machine" or "process" RAM.
                                          Defaults to "machine".
            force_ram_power (int, optional): User-provided RAM power in watts. If provided,
                                           this value is used instead of estimating RAM power.
                                           Defaults to None.
        """
        self._pid = pid
        self._children = children
        self._tracking_mode = tracking_mode
        self._force_ram_power = force_ram_power
        # Check if using ARM architecture
        self.is_arm_cpu = self._detect_arm_cpu()

        if self._force_ram_power is not None:
            logger.info(f"Using user-provided RAM power: {self._force_ram_power} Watts")

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
            # Typical configurations:
            # 4GB = 1x4GB or 2x2GB, use 2 as minimum
            # 8GB = 2x4GB (common) or 1x8GB (less common)
            # 16GB = 2x8GB (common) or 4x4GB or 1x16GB
            # 32GB = 2x16GB or 4x8GB
            if total_gb <= 4:
                return 2  # Minimum 2 DIMMs for standard systems
            elif total_gb <= 8:
                return 2  # 2x4GB is most common
            elif total_gb <= 16:
                return 2  # 2x8GB is most common
            else:  # 17-32GB
                return 4  # 4x8GB is common for 32GB

        # For workstations and small servers (32-128GB)
        if total_gb <= 128:
            # Typical server configurations
            if total_gb <= 64:
                return 4  # 4x16GB
            else:  # 65-128GB
                return 8  # 8x16GB or 4x32GB

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
            # Minimum 3W for ARM
            min_power = 3.0
        else:
            # x86 systems
            base_power_per_dimm = RAM_SLOT_POWER_X86  # Watts
            # Minimum 2 Dimm for x86
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
            Power: kW of power consumption, using either the user-provided value or a power model
        """
        # If user provided a RAM power value, use it directly
        if self._force_ram_power is not None:
            logger.debug(
                f"Using user-provided RAM power: {self._force_ram_power} Watts"
            )
            return Power.from_watts(self._force_ram_power)

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
