"""
Encapsulates external dependencies to retrieve hardware metadata
"""

from abc import abstractmethod, ABC
from dataclasses import dataclass
import logging
from typing import Iterable, List, Dict

from codecarbon.core.units import Power
from codecarbon.core.gpu import get_gpu_details

logger = logging.getLogger(__name__)


@dataclass
class BaseHardware(ABC):
    @property
    @abstractmethod
    def total_power(self) -> Power:
        pass

@dataclass
class GPU(BaseHardware):
    num_gpus: int

    def __repr__(self) -> str:
        return super().__repr__() + " ({})".format(
            ", ".join([d["name"] for d in get_gpu_details()])
        )

    def get_power_for_gpus(self, gpu_ids: Iterable[int]) -> Power:
        """
        Get total power consumed by specific GPUs identified by `gpu_ids`
        :param gpu_ids:
        :return:
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

    @property
    def total_power(self) -> Power:
        return self.get_power_for_gpus(gpu_ids=set(range(self.num_gpus)))

    @classmethod
    def from_utils(cls) -> "GPU":
        return cls(num_gpus=len(get_gpu_details()))


@dataclass
class CPU(BaseHardware):
    @property
    def total_power(self) -> Power:
        pass
