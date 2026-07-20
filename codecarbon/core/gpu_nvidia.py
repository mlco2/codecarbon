import subprocess
from dataclasses import dataclass
from typing import Any, Union

from codecarbon.core.gpu_device import GPUDevice
from codecarbon.external.logger import logger


def is_nvidia_system():
    """Returns True if the system has an nvidia-smi interface."""
    try:
        # Check if nvidia-smi is available
        subprocess.check_output(["nvidia-smi", "--help"])
        return True
    except Exception:
        return False


try:
    import pynvml

    pynvml.nvmlInit()
    PYNVML_AVAILABLE = True
except ImportError:
    pynvml = None
    if is_nvidia_system():
        logger.warning(
            "Nvidia GPU detected but pynvml is not available. "
            "Please install pynvml to get GPU metrics."
        )
    PYNVML_AVAILABLE = False
except Exception:
    pynvml = None
    if is_nvidia_system():
        logger.warning(
            "Nvidia GPU detected but pynvml initialization failed. "
            "Please ensure NVIDIA drivers are properly installed."
        )
    PYNVML_AVAILABLE = False


@dataclass
class NvidiaGPUDevice(GPUDevice):
    def _get_total_energy_consumption(self) -> int:
        """Returns total energy consumption for this GPU in millijoules (mJ) since the driver was last reloaded
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g732ab899b5bd18ac4bfb93c02de4900a
        """
        try:
            return pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)
        except pynvml.NVMLError:
            logger.warning(
                "Failed to retrieve gpu total energy consumption", exc_info=True
            )
            return None

    def _get_gpu_name(self) -> Any:
        """Returns the name of the GPU device
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1ga5361803e044c6fdf3b08523fb6d1481
        """
        try:
            name = pynvml.nvmlDeviceGetName(self.handle)
            return self._to_utf8(name)
        except UnicodeDecodeError:
            return "Unknown GPU"

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
        try:
            return pynvml.nvmlDeviceGetMemoryInfo(self.handle)
        except pynvml.NVMLError_NotSupported:
            # error thrown for the NVIDIA Blackwell GPU of DGX Spark, due to memory sharing -> return defaults instead
            return pynvml.c_nvmlMemory_t(-1, -1, -1)

    def _get_temperature(self) -> int:
        """Returns degrees in the Celsius scale
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g92d1c5182a14dd4be7090e3c1480b121
        """
        return pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)

    def _get_power_usage(self) -> int:
        """Returns power usage in Watts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7ef7dff0ff14238d08a19ad7fb23fc87
        """
        return pynvml.nvmlDeviceGetPowerUsage(self.handle) / 1000

    def _get_power_limit(self) -> Union[int, None]:
        """Returns max power usage in Watts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g263b5bf552d5ec7fcd29a088264d10ad
        """
        try:
            # convert from milliwatts to watts
            return pynvml.nvmlDeviceGetEnforcedPowerLimit(self.handle) / 1000
        except Exception:
            logger.warning("Failed to retrieve gpu power limit", exc_info=True)
            return None

    def _get_gpu_utilization(self):
        """Returns the % of utilization of the kernels during the last sample
        https://docs.nvidia.com/deploy/nvml-api/structnvmlUtilization__t.html#structnvmlUtilization__t
        """
        return pynvml.nvmlDeviceGetUtilizationRates(self.handle).gpu

    def _get_compute_mode(self) -> int:
        """Returns the compute mode of the GPU
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceEnumvs.html#group__nvmlDeviceEnumvs_1gbed1b88f2e3ba39070d31d1db4340233
        """
        return pynvml.nvmlDeviceGetComputeMode(self.handle)

    def _get_compute_processes(self):
        """Returns the list of processes ids having a compute context on the device with the memory used
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g46ceaea624d5c96e098e03c453419d68
        """
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle)
        return [{"pid": p.pid, "used_memory": p.usedGpuMemory} for p in processes]

    def _get_graphics_processes(self):
        """Returns the list of processes ids having a graphics context on the device with the memory used
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7eacf7fa7ba4f4485d166736bf31195e
        """
        processes = pynvml.nvmlDeviceGetGraphicsRunningProcesses(self.handle)
        return [{"pid": p.pid, "used_memory": p.usedGpuMemory} for p in processes]
