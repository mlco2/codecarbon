"""
Encapsulates external dependencies to retrieve hardware metadata
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from codecarbon.core.cpu import IntelPowerGadget
from codecarbon.core.gpu import get_gpu_details
from codecarbon.core.units import Power

logger = logging.getLogger(__name__)


@dataclass
class BaseHardware(ABC):
    @abstractmethod
    def total_power(self) -> Power:
        pass


@dataclass
class GPU(BaseHardware):
    num_gpus: int
    gpu_ids: Optional[List]

    def __repr__(self) -> str:
        return super().__repr__() + " ({})".format(
            ", ".join([d["name"] for d in get_gpu_details()])
        )

    def _get_power_for_gpus(self, gpu_ids: Iterable[int]) -> Power:
        """
        Get total power consumed by specific GPUs identified by `gpu_ids`
        :param gpu_ids:
        :return: power in kW
        """
        all_gpu_details: List[Dict] = get_gpu_details()
        return Power.from_milli_watts(
            sum(
                [
                    gpu_details["power_usage"]
                    for idx, gpu_details in enumerate(all_gpu_details)
                    if idx in gpu_ids
                ]
            )
        )

    def total_power(self) -> Power:
        if self.gpu_ids is not None:
            gpu_ids = self.gpu_ids
            assert set(gpu_ids).issubset(
                set(range(self.num_gpus))
            ), f"CODECARBON Unknown GPU ids {gpu_ids}"
        else:
            gpu_ids = set(range(self.num_gpus))

        return self._get_power_for_gpus(gpu_ids=gpu_ids)

    @classmethod
    def from_utils(cls, gpu_ids: Optional[List] = None) -> "GPU":
        return cls(num_gpus=len(get_gpu_details()), gpu_ids=gpu_ids)


@dataclass
class CPU(BaseHardware):
    def __init__(self, output_dir: str):
        self._output_dir = output_dir
        self._intel_power_gadget = IntelPowerGadget(self._output_dir)

    def _get_power_from_cpus(self) -> Power:
        """
        Get CPU power from Intel Power Gadget
        :return: power in kW
        """
        all_cpu_details: Dict = self._intel_power_gadget.get_cpu_details()

        power = 0
        for metric, value in all_cpu_details.items():
            if re.match("^Processor Power_\d+\(Watt\)$", metric):
                power += value
        logger.debug(f"CODECARBON CPU Power Consumption : {power}")
        return Power.from_watts(power)

    def total_power(self) -> Power:
        return self._get_power_from_cpus()
