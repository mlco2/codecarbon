from collections import namedtuple
from dataclasses import dataclass, field

from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import is_amd_system, is_nvidia_system
from codecarbon.external.logger import logger

USE_AMDSMI = False
USE_PYNVML = False

if is_nvidia_system():
    import pynvml

    USE_PYNVML = True

if is_amd_system():
    import amdsmi

    USE_AMDSMI = True


@dataclass
class GPUDevice:
    handle: any
    gpu_index: int
    # Energy consumed in kWh
    energy_delta: Energy = field(default_factory=lambda: Energy(0))
    # Power based on reading
    power: Power = field(default_factory=lambda: Power(0))
    # Last energy reading in kWh
    last_energy: Energy = field(default_factory=lambda: Energy(0))

    def start(self):
        self.last_energy = self._get_energy_kwh()

    def __post_init__(self):
        self.last_energy = self._get_energy_kwh()
        self._init_static_details()

    def _get_energy_kwh(self):
        return Energy.from_millijoules(self._get_total_energy_consumption())

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
        if USE_PYNVML:
            return pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)
        elif USE_AMDSMI:
            # returns energy in "Energy Status Units" which is equivalent to around 15.3 microjoules
            energy = amdsmi.amdsmi_dev_get_energy_count(self.handle)
            return energy["power"] * energy["counter_resolution"] / 1000
        else:
            raise Exception("No GPU interface available")

    def _get_gpu_name(self):
        """Returns the name of the GPU device
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1ga5361803e044c6fdf3b08523fb6d1481
        """
        if USE_PYNVML:
            name = pynvml.nvmlDeviceGetName(self.handle)
        elif USE_AMDSMI:
            name = amdsmi.amdsmi_get_board_info(self.handle)["manufacturer_name"]
        else:
            raise Exception("No GPU interface available")

        return self._to_utf8(name)

    def _get_uuid(self):
        """Returns the globally unique GPU device UUID
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g72710fb20f30f0c2725ce31579832654
        """
        if USE_PYNVML:
            uuid = pynvml.nvmlDeviceGetUUID(self.handle)
        elif USE_AMDSMI:
            uuid = amdsmi.amdsmi_get_device_uuid(self.handle)
        else:
            raise Exception("No GPU interface available")

        return self._to_utf8(uuid)

    def _get_memory_info(self):
        """Returns memory info in bytes
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
        """
        if USE_PYNVML:
            return pynvml.nvmlDeviceGetMemoryInfo(self.handle)
        elif USE_AMDSMI:
            # returns memory in megabytes (amd-smi metric --mem-usage)
            memory_info = amdsmi.amdsmi_get_vram_usage(self.handle)
            AMDMemory = namedtuple("AMDMemory", ["total", "used", "free"])
            return AMDMemory(
                total=memory_info["vram_total"] * 1024 * 1024,
                used=memory_info["vram_used"] * 1024 * 1024,
                free=(memory_info["vram_total"] - memory_info["vram_used"])
                * 1024
                * 1024,
            )
        else:
            raise Exception("No GPU interface available")

    def _get_temperature(self):
        """Returns degrees in the Celsius scale
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g92d1c5182a14dd4be7090e3c1480b121
        """
        if USE_PYNVML:
            return pynvml.nvmlDeviceGetTemperature(
                self.handle,
                sensor=pynvml.NVML_TEMPERATURE_GPU,
            )
        elif USE_AMDSMI:
            return amdsmi.amdsmi_dev_get_temp_metric(
                self.handle,
                sensor_type=amdsmi.AmdSmiTemperatureType.EDGE,
                metric=amdsmi.AmdSmiTemperatureMetric.CURRENT,
            )
        else:
            raise Exception("No GPU interface available")

    def _get_power_usage(self):
        """Returns power usage in milliwatts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7ef7dff0ff14238d08a19ad7fb23fc87
        """
        if USE_PYNVML:
            return pynvml.nvmlDeviceGetPowerUsage(self.handle)
        elif USE_AMDSMI:
            # returns power in Watts (amd-smi metric --power)
            return (
                amdsmi.amdsmi_get_power_measure(self.handle)["average_socket_power"]
                * 1000
            )
        else:
            raise Exception("No GPU interface available")

    def _get_power_limit(self):
        """Returns max power usage in milliwatts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g263b5bf552d5ec7fcd29a088264d10ad
        """
        try:
            if USE_PYNVML:
                return pynvml.nvmlDeviceGetEnforcedPowerLimit(self.handle)
            elif USE_AMDSMI:
                # returns power limit in Watts (amd-smi static --limit)
                return (
                    amdsmi.amdsmi_get_power_measure(self.handle)["power_limit"] * 1000
                )
        except Exception:
            return None

    def _get_gpu_utilization(self):
        """Returns the % of utilization of the kernels during the last sample
        https://docs.nvidia.com/deploy/nvml-api/structnvmlUtilization__t.html#structnvmlUtilization__t
        """
        if USE_PYNVML:
            return pynvml.nvmlDeviceGetUtilizationRates(self.handle).gpu
        elif USE_AMDSMI:
            return amdsmi.amdsmi_get_gpu_activity(self.handle)["gfx_activity"]
        else:
            raise Exception("No GPU interface available")

    def _get_compute_mode(self):
        """Returns the compute mode of the GPU
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceEnumvs.html#group__nvmlDeviceEnumvs_1gbed1b88f2e3ba39070d31d1db4340233
        """
        if USE_PYNVML:
            return pynvml.nvmlDeviceGetComputeMode(self.handle)
        elif USE_AMDSMI:
            return None
        else:
            raise Exception("No GPU interface available")

    def _get_compute_processes(self):
        """Returns the list of processes ids having a compute context on the device with the memory used
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g46ceaea624d5c96e098e03c453419d68
        """
        try:
            if USE_PYNVML:
                processes = pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle)
                return [
                    {"pid": p.pid, "used_memory": p.usedGpuMemory} for p in processes
                ]
            elif USE_AMDSMI:
                processes_handles = amdsmi.amdsmi_get_process_list(self.handle)
                processes_info = [
                    amdsmi.amdsmi_get_process_info(self.handle, p)
                    for p in processes_handles
                ]
                return [
                    {"pid": p["pid"], "used_memory": p["memory_usage"]["vram_usage"]}
                    for p in processes_info
                ]
        except Exception:
            return []

    def _get_graphics_processes(self):
        """Returns the list of processes ids having a graphics context on the device with the memory used
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7eacf7fa7ba4f4485d166736bf31195e
        """
        try:
            if USE_PYNVML:
                processes = pynvml.nvmlDeviceGetGraphicsRunningProcesses(self.handle)
                return [
                    {"pid": p.pid, "used_memory": p.usedGpuMemory} for p in processes
                ]
            elif USE_AMDSMI:
                processes_handles = amdsmi.amdsmi_get_process_list(self.handle)
                processes_info = [
                    amdsmi.amdsmi_get_process_info(self.handle, p)
                    for p in processes_handles
                ]
                return [
                    {"pid": p["pid"], "used_memory": p["memory_usage"]["vram_usage"]}
                    for p in processes_info
                    if p["engine_usage"]["gfx"] > 0
                ]
        except Exception:
            return []


class AllGPUDevices:
    devices = []
    device_count:int = 0
    
    def __init__(self):
        self.devices = []
        if is_gpu_details_available():
            if USE_PYNVML:
                logger.debug("Nvidia GPU available. Starting setup")
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                for i in range(self.device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    gpu_device = GPUDevice(handle=handle, gpu_index=i)
                    self.devices.append(gpu_device)
            if USE_AMDSMI:
                logger.debug("AMD GPU available. Starting setup")
                amdsmi.amdsmi_init()
                self.device_count = len(amdsmi.amdsmi_get_device_handles())
                for i in range(self.device_count):
                    handle = amdsmi.amdsmi_get_device_handles()[i]
                    gpu_device = GPUDevice(handle=handle, gpu_index=i)
                    self.devices.append(gpu_device)
            else:
                logger.error("No GPU interface available")
        else:
            logger.error("There is no GPU available")
        self.device_count = len(self.devices)

        

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
            for i in range(self.device_count):
                gpu_device = self.devices[i]
                devices_static_info.append(gpu_device.get_static_details())
            return devices_static_info

        except Exception:
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
            for i in range(self.device_count):
                gpu_device: GPUDevice = self.devices[i]
                devices_info.append(gpu_device.get_gpu_details())
            return devices_info

        except Exception:
            logger.warning("Failed to retrieve gpu information", exc_info=True)
            return []

    def get_delta(self, last_duration: Time):
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
            for i in range(self.device_count):
                gpu_device: GPUDevice = self.devices[i]
                devices_info.append(gpu_device.delta(last_duration))
            return devices_info

        except Exception:
            logger.warning("Failed to retrieve gpu information", exc_info=True)
            return []


def is_gpu_details_available():
    """Returns True if the GPU details are available."""
    try:
        if USE_PYNVML:
            pynvml.nvmlInit()
            return True
        elif USE_AMDSMI:
            amdsmi.amdsmi_init()
            return True
        else:
            return False

    except Exception:
        return False
