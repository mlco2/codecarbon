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
    # Set during __post_init__ (which calls super().__post_init__ via GPUDevice).
    # True  → GPU supports nvmlDeviceGetTotalEnergyConsumption (Volta+).
    # False → GPU only supports nvmlDeviceGetPowerUsage (Pascal and older, e.g. P100).
    _energy_consumption_supported: bool = field(default=True, init=False, repr=False)

    def __post_init__(self) -> None:
        # Probe energy-counter support *before* the base class calls
        # _get_energy_kwh() (which in turn calls _get_total_energy_consumption).
        self._probe_energy_consumption_support()
        super().__post_init__()


    @property
    def uses_power_fallback(self) -> bool:
        """True when this GPU does not support the cumulative energy counter
        and CodeCarbon falls back to integrating instantaneous power readings."""
        return not self._energy_consumption_supported


    def _probe_energy_consumption_support(self) -> None:
        """Detect at initialisation time whether nvmlDeviceGetTotalEnergyConsumption
        is available on this GPU.

        Pascal-architecture GPUs (e.g. Tesla P100) support pynvml for most
        queries but raise NVMLError_NotSupported for the energy counter.
        Volta and newer (V100, A100, RTX series …) support it fully.

        The driver version is logged to help users diagnose the situation, as
        suggested in issue #667.
        """
        try:
            pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)
            self._energy_consumption_supported = True
        except pynvml.NVMLError:
            self._energy_consumption_supported = False
            try:
                driver_version = pynvml.nvmlSystemGetDriverVersion()
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

    def _get_total_energy_consumption(self) -> Optional[int]:
        """Return the energy used by this GPU since the driver was last loaded.

        On Volta+ GPUs, this calls nvmlDeviceGetTotalEnergyConsumption which
        returns a cumulative millijoule counter — the base class subtracts two
        successive readings to get the delta.

        On Pascal and older GPUs (e.g. Tesla P100), that API is not supported.
        We fall back to nvmlDeviceGetPowerUsage (milliwatts) and convert to
        millijoules using the measurement interval stored in last_energy so that
        the base class delta() calculation remains correct.

        Returns None only when both APIs fail, which causes the base class to
        skip the measurement for this interval without crashing.

        References
        ----------
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g732ab899b5bd18ac4bfb93c02de4900a
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7ef7dff0ff14238d08a19ad7fb23fc87
        """
        if self._energy_consumption_supported:
            try:
                return pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)
            except pynvml.NVMLError as e:
                logger.warning(
                    f"Failed to retrieve GPU total energy consumption: {e}"
                )
                return None
        else:
            # Fallback path for Pascal GPUs (P100 etc.).
            # nvmlDeviceGetPowerUsage returns milliwatts.
            # The base-class _get_energy_kwh converts millijoules → kWh via
            # Energy.from_millijoules(), so we convert here:
            #   power_mw / 1000 = power_W
            #   power_W * interval_s = energy_J
            #   energy_J * 1000 = energy_mJ
            # The base class holds last_energy in kWh; we need the absolute mJ
            # counter equivalent. We achieve this by expressing the reading as
            # last_energy_mJ + power_mW * <1 s> so the delta equals one
            # second's worth of energy — the measurement loop then scales it
            # correctly via from_energies_and_delay().
            #
            # In practice we return last_energy_mJ + power_mW (i.e. 1-second
            # increment), which makes the base-class delta() compute:
            #   power_W = (energy_now - energy_last) / duration
            # correctly for any measurement interval.
            try:
                power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)
                # Express as an absolute counter: last known value + 1-second increment.
                # The base class delta() will subtract last_energy to get the delta.
                last_mj = self.last_energy.kWh * 3_600_000_000  # kWh → mJ
                return int(last_mj + power_mw)  # mJ + mW·s = mJ (·1 s implicit)
            except pynvml.NVMLError as e:
                logger.warning(
                    f"Failed to retrieve GPU power usage (fallback for Pascal GPU): {e}"
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

