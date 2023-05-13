# -*- coding: utf-8 -*-

# Copyright (C) 2020 [COMET-ML]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from dataclasses import dataclass, field

import pynvml

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger


@dataclass
class GPUDevice:
    # Energy consumed in kWh
    energy_delta: Energy = field(default_factory=lambda: Energy(0))
    # Power based on reading
    power: Power = field(default_factory=lambda: Power(0))
    # Last energy reading in kWh
    last_energy: Energy = field(default_factory=lambda: Energy(0))
    handle: any
    gpu_index: int

    def __post_init__(self):
        self.last_energy = self._get_energy_kwh()
        self._init_static_details()

    def _get_energy_kwh(self):
        return Energy.from_millijoules(self._get_energy_consumption())

    def delta(self, duration: Time) -> dict:
        """
        Compute the energy/power used since last call.
        """
        new_last_energy = energy = self._get_energy_kwh()
        self.power = self.power.from_energies_and_delay(
            energy, self.last_energy, duration
        )
        self.energy_delta = energy - self.last_energy
        self.last_energy = new_last_energy
        return {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "delta_energy_consumption": self.energy_delta,
            "power_usage": self.power,
        }

    def get_static_details(self):
        return {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "total_memory": self._total_memory,
            "power_limit": self._power_limit,
            "gpu_index": self.gpu_index,
        }

    def _init_static_details(self):
        self._gpu_name = self._get_gpu_name()
        self._uuid = self._get_uuid()
        self._power_limit = self._get_power_limit()
        # Get the memory
        memory = self._get_memory_info()
        self._total_memory = memory.total

    def get_gpu_details(self):
        # Memory
        memory = self._get_memory_info()

        device_details = {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "free_memory": memory.free,
            "total_memory": memory.total,
            "used_memory": memory.used,
            "temperature": self._get_temperature(),
            "power_usage": self._get_power_usage(),
            "power_limit": self._power_limit,
            "total_energy_consumption": self._get_total_energy_consumption(),
            "gpu_utilization": self._get_gpu_utilization(),
            "compute_mode": self._get_compute_mode(),
            "compute_processes": self._get_compute_processes(),
            "graphics_processes": self._get_graphics_processes(),
        }
        return device_details

    def _to_utf8(self, str_or_bytes):
        if hasattr(str_or_bytes, "decode"):
            return str_or_bytes.decode("utf-8", errors="replace")

        return str_or_bytes

    def _get_total_energy_consumption(self):
        """Returns total energy consumption for this GPU in millijoules (mJ) since the driver was last reloaded
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g732ab899b5bd18ac4bfb93c02de4900a
        """
        return pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)

    def _get_gpu_name(self):
        """Returns the name of the GPU device
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1ga5361803e044c6fdf3b08523fb6d1481
        """
        name = pynvml.nvmlDeviceGetName(self.handle)
        return self._to_utf8(name)

    def _get_uuid(self):
        """Returns the globally unique GPU device UUID
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g72710fb20f30f0c2725ce31579832654
        """
        uuid = pynvml.nvmlDeviceGetUUID(self.handle)
        return self._to_utf8(uuid)

    def _get_memory_info(self):
        """Returns memory info in bytes
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
        """
        return pynvml.nvmlDeviceGetMemoryInfo(self.handle)

    def _get_temperature(self):
        """Returns degrees in the Celsius scale
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g92d1c5182a14dd4be7090e3c1480b121
        """
        return pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)

    def _get_power_usage(self):
        """Returns power usage in milliwatts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7ef7dff0ff14238d08a19ad7fb23fc87
        """
        return pynvml.nvmlDeviceGetPowerUsage(self.handle)

    def _get_power_limit(self):
        """Returns max power usage in milliwatts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g263b5bf552d5ec7fcd29a088264d10ad
        """
        try:
            return pynvml.nvmlDeviceGetEnforcedPowerLimit(self.handle)
        except Exception:
            return None

    def _get_gpu_utilization(self):
        """Returns the % of utilization of the kernels during the last sample
        https://docs.nvidia.com/deploy/nvml-api/structnvmlUtilization__t.html#structnvmlUtilization__t
        """
        return pynvml.nvmlDeviceGetUtilizationRates(self.handle).gpu

    def _get_compute_mode(self):
        """Returns the compute mode of the GPU
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceEnumvs.html#group__nvmlDeviceEnumvs_1gbed1b88f2e3ba39070d31d1db4340233
        """
        return pynvml.nvmlDeviceGetComputeMode(self.handle)

    def _get_compute_processes(self):
        """Returns the list of processes ids having a compute context on the
        device with the memory used
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g46ceaea624d5c96e098e03c453419d68
        """
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle)

        return [{"pid": p.pid, "used_memory": p.usedGpuMemory} for p in processes]

    def _get_graphics_processes(self):
        """Returns the list of processes ids having a graphics context on the
        device with the memory used
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7eacf7fa7ba4f4485d166736bf31195e
        """
        processes = pynvml.nvmlDeviceGetGraphicsRunningProcesses(self.handle)

        return [{"pid": p.pid, "used_memory": p.usedGpuMemory} for p in processes]


class AllGPUDevices:
    def __init__(self):
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        self.devices = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            gpu_device = GPUDevice(handle=handle, gpu_index=i)
            self.devices.append(gpu_device)

    def get_gpu_static_info(self):
        """Get all GPUs static information.
        >>> get_gpu_static_info()
        [
            {
                "name": "Tesla V100-SXM2-16GB",
                "uuid": "GPU-4e817856-1fb8-192a-7ab7-0e0e4476c184",
                "total_memory": 16945512448,
                "power_limit": 300000,
                "gpu_index": 0,
            }
        ]
        """
        try:
            devices_static_info = []
            for i in range(self.devices.length):
                gpu_device = self.devices[i]
                devices_static_info.append(gpu_device.get_static_details())
            return devices_static_info

        except pynvml.NVMLError:
            logger.warning("Failed to retrieve gpu static info", exc_info=True)
            return []

    def get_gpu_details(self):
        """Get all GPUs instantaneous metrics
        >>> get_gpu_details()
        [
            {
                "name": "Tesla V100-SXM2-16GB",
                "uuid": "GPU-4e817856-1fb8-192a-7ab7-0e0e4476c184",
                "free_memory": 16945381376,
                "total_memory": 16945512448,
                "used_memory": 131072,
                "temperature": 28,
                "total_energy_consumption":2000,
                "power_usage": 42159,
                "power_limit": 300000,
                "gpu_utilization": 0,
                "compute_mode": 0,
                "compute_processes": [],
                "graphics_processes": [],
            }
        ]
        """
        try:
            devices_info = []
            for i in range(self.devices.length):
                gpu_device = self.devices[i]
                devices_info.append(gpu_device.get_gpu_details())
            return devices_info

        except pynvml.NVMLError:
            logger.warning("Failed to retrieve gpu information", exc_info=True)
            return []

    def get_delta(self, last_duration: float):
        """Get difference since last time this function was called
        >>> get_delta()
        [
            {
                "name": "Tesla V100-SXM2-16GB",
                "uuid": "GPU-4e817856-1fb8-192a-7ab7-0e0e4476c184",
                "delta_energy_consumption":2000,
                "power_usage": 42159,
            }
        ]
        """
        try:
            devices_info = []
            for i in range(self.devices.length):
                gpu_device = self.devices[i]
                devices_info.append(gpu_device.delta(last_duration))
            return devices_info

        except pynvml.NVMLError:
            logger.warning("Failed to retrieve gpu information", exc_info=True)
            return []


def is_gpu_details_available():
    """Returns True if the GPU details are available."""
    try:
        pynvml.nvmlInit()
        return True

    except pynvml.NVMLError:
        return False
