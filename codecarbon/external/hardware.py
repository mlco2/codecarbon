"""
Encapsulates external dependencies to retrieve hardware metadata
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from codecarbon.core.gpu import AllGPUDevices
from codecarbon.core.powermetrics import ApplePowermetrics
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger

B_TO_GB = 1024 * 1024 * 1024


@dataclass
class BaseHardware(ABC):
    @abstractmethod
    def total_power(self) -> Power:
        raise NotImplementedError()
        # pass

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
        if self.gpu_ids is not None:
            uuids_to_ids = {
                gpu.get("uuid"): gpu.get("gpu_index")
                for gpu in self.devices.get_gpu_static_info()
            }
            monitored_gpu_ids = []

            for gpu_id in self.gpu_ids:
                found_gpu_id = False
                # Does it look like an index into the number of GPUs on the system?
                if isinstance(gpu_id, int) or gpu_id.isdigit():
                    gpu_id = int(gpu_id)
                    if 0 <= gpu_id < self.num_gpus:
                        monitored_gpu_ids.append(gpu_id)
                        found_gpu_id = True
                # Does it match a prefix of any UUID on the system after stripping any 'MIG-'
                # id prefix per https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#cuda-environment-variables ?
                else:
                    stripped_gpu_id_str = gpu_id.lstrip("MIG-")
                    for uuid, id in uuids_to_ids.items():
                        if uuid.startswith(stripped_gpu_id_str):
                            logger.debug(
                                f"Matching GPU ID {stripped_gpu_id_str} (originally {gpu_id}) against {uuid} for GPU index {id}"
                            )
                            monitored_gpu_ids.append(id)
                            found_gpu_id = True
                            break
                if not found_gpu_id:
                    logger.warning(
                        f"GPU with ID '{gpu_id}' not found or invalid. It will be ignored."
                    )

            monitored_gpu_ids = sorted(list(set(monitored_gpu_ids)))
            self.gpu_ids = monitored_gpu_ids
            return monitored_gpu_ids
        else:
            return list(range(self.num_gpus))

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
                f"You have {gpus.num_gpus} GPUs but we will monitor only {len(new_gpu_ids)} ({new_gpu_ids}) of them. Check your configuration."
            )
        return cls(gpu_ids=new_gpu_ids)


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
