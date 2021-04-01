"""
Encapsulates external dependencies to retrieve hardware metadata
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import cpuinfo

from codecarbon.core.cpu import IntelPowerGadget, IntelRAPL
from codecarbon.core.gpu import get_gpu_details
from codecarbon.core.units import Power
from codecarbon.input import DataSource

POWER_CONSTANT = 85

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

        gpu_power = self._get_power_for_gpus(gpu_ids=gpu_ids)
        logger.info(f"CODECARBON GPU Power Consumption : {gpu_power}")
        return gpu_power

    @classmethod
    def from_utils(cls, gpu_ids: Optional[List] = None) -> "GPU":
        return cls(num_gpus=len(get_gpu_details()), gpu_ids=gpu_ids)


@dataclass
class CPU(BaseHardware):
    def __init__(self, output_dir: str, mode: str):
        self._output_dir = output_dir
        self._mode = mode
        if self._mode == "intel_power_gadget":
            self._intel_interface = IntelPowerGadget(self._output_dir)
        elif self._mode == "intel_rapl":
            self._intel_interface = IntelRAPL()

    def _get_power_from_cpus(self) -> Power:
        """
        Get CPU power from Intel Power Gadget
        :return: power in kW
        """
        if self._mode == "constant":
            logger.warning(
                "CODECARBON : No CPU/GPU tracking mode found. Falling back on CPU constant mode."
            )
            return self._get_power_from_constant()

        all_cpu_details: Dict = self._intel_interface.get_cpu_details()

        power = 0
        for metric, value in all_cpu_details.items():
            if re.match("^Processor Power_\d+\(Watt\)$", metric):
                power += value
        return Power.from_watts(power)

    def _get_power_from_constant(self) -> Power:
        """
        Get CPU power from constant mode
        :return: power in KW
        """
        cpu_info = cpuinfo.get_cpu_info()
        if cpu_info:
            model_raw = cpu_info["brand_raw"]
            model = model_raw.split(" CPU")[0].replace("(R)", "").replace("(TM)", "")
            cpu_power_df = DataSource().get_cpu_power_data()
            cpu_power_df_model = cpu_power_df[cpu_power_df["Name"] == model]
            if len(cpu_power_df_model) > 0:
                power = cpu_power_df_model["TDP"].tolist()[0]
            else:
                logger.warning(
                    f"CPU : Failed to match CPU TDP constant. Falling back on global constant ({POWER_CONSTANT}w)."
                )
                power = POWER_CONSTANT
        else:
            power = POWER_CONSTANT
        return Power.from_watts(power)

    def total_power(self) -> Power:
        cpu_power = self._get_power_from_cpus()
        logger.info(f"CODECARBON CPU Power Consumption : {cpu_power}")
        return cpu_power

    @classmethod
    def from_utils(cls, output_dir: str, mode: str) -> "CPU":
        return cls(output_dir=output_dir, mode=mode)
