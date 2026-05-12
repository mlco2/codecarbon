import subprocess
from dataclasses import dataclass, field
from typing import Any, Optional, Union

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
    # Tracks whether nvmlDeviceGetTotalEnergyConsumption is supported.
    # None  = not yet determined (set on first call)
    # True  = works fine (Volta+ GPUs: V100, A100, RTX series, etc.)
    # False = permanently unsupported; use power-usage fallback (Pascal/P100)
    _energy_consumption_supported: Optional[bool] = field(
        default=None, init=False, repr=False
    )

    @property
    def uses_power_fallback(self) -> bool:
        """True when this GPU does not support the cumulative energy counter
        and CodeCarbon falls back to integrating instantaneous power readings."""
        return self._energy_consumption_supported is False

    def _get_total_energy_consumption(self) -> Optional[int]:
        """Returns total energy consumption for this GPU in millijoules (mJ)
        since the driver was last reloaded.

        On Volta+ GPUs uses nvmlDeviceGetTotalEnergyConsumption (cumulative mJ
        counter). On Pascal GPUs (e.g. Tesla P100) that API raises
        NVMLError_NotSupported; we detect this on the FIRST call only, emit a
        single clear warning with the driver version (issue #667), and
        permanently switch to nvmlDeviceGetPowerUsage for all future calls.

        Generic / transient NVMLErrors (e.g. "System is not in ready state")
        are treated the same as before: log a warning and return None for that
        interval. The fallback is NOT activated — these errors may be temporary.

        Returns None only when the API call fails, so the base class skips the
        interval gracefully without crashing.

        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g732ab899b5bd18ac4bfb93c02de4900a
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7ef7dff0ff14238d08a19ad7fb23fc87
        """
        # --- Supported path (Volta+ or not yet determined) ---
        if self._energy_consumption_supported is not False:
            try:
                result = pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)
                self._energy_consumption_supported = True
                return result
            except pynvml.NVMLError as e:
                # NVMLError_NotSupported is a permanent hardware limitation
                # (P100 and older Pascal GPUs). Switch to power-usage fallback.
                # Other NVMLErrors are transient — do NOT activate the fallback.
                # Use getattr for compatibility with fake pynvml modules in tests.
                _not_supported_cls = getattr(pynvml, "NVMLError_NotSupported", None)
                if _not_supported_cls is not None and isinstance(e, _not_supported_cls):
                    self._energy_consumption_supported = False
                    self._log_fallback_warning()
                    # Fall through to the power-usage path below.
                else:
                    # Transient error (e.g. "System is not in ready state").
                    # Do NOT activate the fallback — retry next interval.
                    logger.warning(
                        "Failed to retrieve gpu total energy consumption", exc_info=True
                    )
                    return None

        # --- Fallback path (Pascal / P100 and older) ---
        # nvmlDeviceGetPowerUsage returns instantaneous milliwatts.
        # We return (last_energy_mJ + power_mW) so the base-class delta()
        # subtracts two successive readings and gets exactly power_mW mJ,
        # which from_energies_and_delay() scales to the actual interval.
        try:
            power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)
            last_mj = self.last_energy.kWh * 3_600_000_000  # kWh -> mJ
            return int(last_mj + power_mw)
        except pynvml.NVMLError as e:
            logger.warning(
                f"Failed to retrieve GPU power usage (fallback for Pascal GPU): {e}"
            )
            return None

    def _log_fallback_warning(self) -> None:
        """Log a single warning when permanently switching to power-usage fallback.
        Includes the driver version as suggested in GitHub issue #667."""
        try:
            _get_driver = getattr(pynvml, "nvmlSystemGetDriverVersion", None)
            driver_version = _get_driver() if _get_driver is not None else "unknown"
            if isinstance(driver_version, bytes):
                driver_version = driver_version.decode("utf-8", errors="replace")
        except Exception:
            driver_version = "unknown"
        logger.warning(
            "nvmlDeviceGetTotalEnergyConsumption is not supported on this GPU "
            f"(driver version: {driver_version}). "
            "This is expected for Pascal-architecture GPUs such as the Tesla P100. "
            "Falling back to power-usage integration via nvmlDeviceGetPowerUsage. "
            "Energy measurements will remain accurate; they are computed by "
            "integrating instantaneous power readings over time."
        )

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
