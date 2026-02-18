import subprocess
from collections import namedtuple
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Union

from codecarbon.core.units import Energy, Power, Time
from codecarbon.external.logger import logger


def is_rocm_system():
    """Returns True if the system has an rocm-smi interface."""
    try:
        # Check if rocm-smi is available
        subprocess.check_output(["rocm-smi", "--help"])
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


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
    if is_nvidia_system():
        logger.warning(
            "Nvidia GPU detected but pynvml is not available. "
            "Please install pynvml to get GPU metrics."
        )
    PYNVML_AVAILABLE = False
except Exception:
    if is_nvidia_system():
        logger.warning(
            "Nvidia GPU detected but pynvml initialization failed. "
            "Please ensure NVIDIA drivers are properly installed."
        )
    PYNVML_AVAILABLE = False

try:
    import amdsmi

    AMDSMI_AVAILABLE = True
except ImportError:
    if is_rocm_system():
        logger.warning(
            "AMD GPU detected but amdsmi is not available. "
            "Please install amdsmi to get GPU metrics."
        )
    AMDSMI_AVAILABLE = False
except AttributeError as e:
    # In some environments, amdsmi may be present but not properly configured, leading to AttributeError when importing
    logger.warning(
        "AMD GPU detected but amdsmi is not properly configured. "
        "Please ensure amdsmi is correctly installed to get GPU metrics."
        "Tips : check consistency between Python amdsmi package and ROCm versions, and ensure AMD drivers are up to date."
        f" Error: {e}"
    )
    AMDSMI_AVAILABLE = False


@dataclass
class GPUDevice:
    """
    Represents a GPU device with associated energy and power metrics.

    Attributes:
        handle (any): An identifier for the GPU device.
        gpu_index (int): The index of the GPU device in the system.
        energy_delta (Energy): The amount of energy consumed by the GPU device
            since the last measurement, expressed in kilowatt-hours (kWh).
            Defaults to an initial value of 0 kWh.
        power (Power): The current power consumption of the GPU device,
            measured in watts (W). Defaults to an initial value of 0 W.
        last_energy (Energy): The last recorded energy reading for the GPU
            device, expressed in kilowatt-hours (kWh). This is used to
            calculate `energy_delta`. Defaults to an initial value of 0 kWh.
    """

    handle: any
    gpu_index: int
    # Power based on reading
    power: Power = field(default_factory=lambda: Power(0))
    # Energy consumed in kWh
    energy_delta: Energy = field(default_factory=lambda: Energy(0))
    # Last energy reading in kWh
    last_energy: Energy = field(default_factory=lambda: Energy(0))

    def start(self) -> None:
        self.last_energy = self._get_energy_kwh()

    def __post_init__(self) -> None:
        self.last_energy = self._get_energy_kwh()
        self._init_static_details()

    def _get_energy_kwh(self) -> Energy:
        total_energy_consumption = self._get_total_energy_consumption()
        if total_energy_consumption is None:
            return self.last_energy
        return Energy.from_millijoules(total_energy_consumption)

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
            "gpu_index": self.gpu_index,
            "delta_energy_consumption": self.energy_delta,
            "power_usage": self.power,
        }

    def get_static_details(self) -> Dict[str, Any]:
        return {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "total_memory": self._total_memory,
            "power_limit": self._power_limit,
            "gpu_index": self.gpu_index,
        }

    def _init_static_details(self) -> None:
        self._gpu_name = self._get_gpu_name()
        self._uuid = self._get_uuid()
        self._power_limit = self._get_power_limit()
        # Get the memory
        memory = self._get_memory_info()
        self._total_memory = memory.total

    def get_gpu_details(self) -> Dict[str, Any]:
        # Memory
        memory = self._get_memory_info()

        device_details = {
            "name": self._gpu_name,
            "uuid": self._uuid,
            "gpu_index": self.gpu_index,
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

    def _to_utf8(self, str_or_bytes) -> Any:
        if hasattr(str_or_bytes, "decode"):
            return str_or_bytes.decode("utf-8", errors="replace")

        return str_or_bytes


@dataclass
class NvidiaGPUDevice(GPUDevice):

    def _get_total_energy_consumption(self) -> int:
        """Returns total energy consumption for this GPU in millijoules (mJ) since the driver was last reloaded
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g732ab899b5bd18ac4bfb93c02de4900a
        """
        if USE_PYNVML:
            try:
                return pynvml.nvmlDeviceGetTotalEnergyConsumption(self.handle)
            except pynvml.NVMLError:
                logger.warning(
                    "Failed to retrieve gpu total energy consumption", exc_info=True
                )
                return None
        elif USE_AMDSMI:
            # returns energy in "Energy Status Units" which is equivalent to around 15.3 microjoules
            energy = amdsmi.amdsmi_dev_get_energy_count(self.handle)
            return energy["power"] * energy["counter_resolution"] / 1000
        else:
            raise Exception("No GPU interface available")

    def _get_gpu_name(self) -> Any:
        """Returns the name of the GPU device
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1ga5361803e044c6fdf3b08523fb6d1481
        """
        if USE_PYNVML:
            try:
                name = pynvml.nvmlDeviceGetName(self.handle)
                return self._to_utf8(name)
            except UnicodeDecodeError:
                return "Unknown GPU"
        elif USE_AMDSMI:
            try:
                name = amdsmi.amdsmi_get_board_info(self.handle)["manufacturer_name"]
                return self._to_utf8(name)
            except UnicodeDecodeError:
                return "Unknown GPU"
        else:
            raise Exception("No GPU interface available")

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
        if USE_PYNVML:
            try:
                return pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            except pynvml.NVMLError_NotSupported:
                # error thrown for the NVIDIA Blackwell GPU of DGX Spark, due to memory sharing -> return defaults instead
                return pynvml.c_nvmlMemory_t(-1, -1, -1)
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

    def _get_temperature(self) -> int:
        """Returns degrees in the Celsius scale
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g92d1c5182a14dd4be7090e3c1480b121
        """
        return pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)

    def _get_power_usage(self) -> int:
        """Returns power usage in milliwatts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g7ef7dff0ff14238d08a19ad7fb23fc87
        """
        return pynvml.nvmlDeviceGetPowerUsage(self.handle)

    def _get_power_limit(self) -> Union[int, None]:
        """Returns max power usage in milliwatts
        https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g263b5bf552d5ec7fcd29a088264d10ad
        """
        try:
            return pynvml.nvmlDeviceGetEnforcedPowerLimit(self.handle)
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


class AMDGPUDevice(GPUDevice):
    def _is_amdsmi_not_initialized_error(self, error: Exception) -> bool:
        ret_code = getattr(error, "ret_code", None)
        if ret_code == 32:
            return True
        error_message = str(error)
        return "AMDSMI_STATUS_NOT_INIT" in error_message or "| 32 |" in error_message

    def _call_amdsmi_with_reinit(self, func: Callable, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except amdsmi.amdsmi_exception.AmdSmiLibraryException as error:
            if not self._is_amdsmi_not_initialized_error(error):
                raise

            logger.warning(
                "AMDSMI reported device not initialized. Reinitializing and retrying once.",
                exc_info=True,
            )
            amdsmi.amdsmi_init()
            return func(*args, **kwargs)

    def _get_gpu_metrics_info(self):
        """Helper function to get all GPU metrics at once, to minimize the number of calls to amdsmi and reduce the risk of hitting not initialized error"""
        return self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_gpu_metrics_info, self.handle
        )

    def _get_total_energy_consumption(self):
        """Returns energy in millijoules.
        amdsmi_get_energy_count returns accumulated energy counter and its resolution.
        Energy = counter_value * counter_resolution (in µJ), convert to mJ.
        """
        try:
            energy_count = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_energy_count, self.handle
            )
            # The amdsmi library returns a dict with energy counter and resolution
            # The counter is the actual accumulated value, resolution tells us how much each unit is worth
            counter_value = energy_count.get("energy_accumulator", 0)
            counter_resolution_uj = energy_count.get("counter_resolution", 0)
            if counter_value == 0 and counter_resolution_uj > 0:
                # In some cases, the energy_accumulator is 0 but it exist in the metrics info, try to get it from there as a fallback
                metrics_info = self._get_gpu_metrics_info()
                counter_value = metrics_info.get("energy_accumulator", 0)
                logger.debug(
                    f"Energy accumulator value from metrics info : {counter_value} for GPU {self._gpu_name} with handle {self.handle} {metrics_info=}"
                )

            if counter_value == 0 or counter_resolution_uj == 0:
                logger.warning(
                    f"Failed to retrieve AMD GPU energy accumulator. energy_count: {energy_count} {counter_value=} {counter_resolution_uj=}",
                    exc_info=True,
                )
                return None

            # energy_in_µJ = counter_value * resolution_in_µJ
            # Divide by 1000 to convert µJ to mJ
            energy_mj = counter_value * counter_resolution_uj / 1000
            return energy_mj
        except Exception:
            logger.warning(
                "Failed to retrieve AMD GPU total energy consumption", exc_info=True
            )
            return None

    def _get_gpu_name(self):
        """Returns the name of the GPU device"""
        try:
            asic_info = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_gpu_asic_info, self.handle
            )
            name = asic_info.get("market_name", "Unknown GPU")
        except Exception:
            name = "Unknown GPU"
        return self._to_utf8(name)

    def _get_uuid(self):
        """Returns the globally unique GPU device UUID"""
        uuid = self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_gpu_device_uuid, self.handle
        )
        return self._to_utf8(uuid)

    def _get_memory_info(self):
        """Returns memory info in bytes"""
        memory_info = self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_gpu_vram_usage, self.handle
        )
        AMDMemory = namedtuple("AMDMemory", ["total", "used", "free"])
        # vram_total and vram_used are already in MB
        total_mb = memory_info["vram_total"]
        used_mb = memory_info["vram_used"]
        return AMDMemory(
            total=total_mb * 1024 * 1024,
            used=used_mb * 1024 * 1024,
            free=(total_mb - used_mb) * 1024 * 1024,
        )

    def _get_temperature(self):
        """Returns degrees in the Celsius scale. Returns temperature in millidegrees Celsius."""
        # amdsmi_get_temp_metric returns temperature in millidegrees Celsius
        temp_milli_celsius = self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_temp_metric,
            self.handle,
            sensor_type=amdsmi.AmdSmiTemperatureType.EDGE,
            metric=amdsmi.AmdSmiTemperatureMetric.CURRENT,
        )
        # Convert from millidegrees to degrees
        temp = temp_milli_celsius // 1000
        # In some cases, the edge temperature can be 0 or not available, try to get it from metrics info as a fallback
        if temp == 0:
            metrics_info = self._get_gpu_metrics_info()
            temp_celsius = metrics_info.get("temperature_edge", 0)
            temp = temp_celsius
        return temp

    def _get_power_usage(self):
        """Returns power usage in milliwatts"""
        # amdsmi_get_power_info returns power in watts, convert to milliwatts
        power_info = self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_power_info, self.handle
        )
        power = int(power_info["average_socket_power"] * 1000)
        if power == 0:
            # In some cases, the average_socket_power can be 0 or not available, try to get it from metrics info as a fallback
            metrics_info = self._get_gpu_metrics_info()
            power = int(metrics_info.get("average_socket_power", 0) * 1000)
        return power

    def _get_power_limit(self):
        """Returns max power usage in milliwatts"""
        # Get power cap info which contains power_cap in uW (microwatts)
        try:
            power_cap_info = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_power_cap_info, self.handle
            )
            # power_cap is in uW, convert to mW
            return int(power_cap_info["power_cap"] / 1000)
        except Exception:
            logger.warning("Failed to retrieve gpu power cap", exc_info=True)
            return None

    def _get_gpu_utilization(self):
        """Returns the % of utilization of the kernels during the last sample"""
        activity = self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_gpu_activity, self.handle
        )
        return activity["gfx_activity"]

    def _get_compute_mode(self):
        """Returns the compute mode of the GPU"""
        return None

    def _get_compute_processes(self):
        """Returns the list of processes ids having a compute context on the device with the memory used"""
        try:
            processes = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_gpu_process_list, self.handle
            )
            return [{"pid": p["pid"], "used_memory": p["mem"]} for p in processes]
        except Exception:
            # logger.warning("Failed to retrieve gpu compute processes", exc_info=True)
            return []

    def _get_graphics_processes(self):
        """Returns the list of processes ids having a graphics context on the device with the memory used"""
        try:
            processes = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_gpu_process_list, self.handle
            )
            return [
                {"pid": p["pid"], "used_memory": p["mem"]}
                for p in processes
                if p["engine_usage"].get("gfx", 0) > 0
            ]
        except Exception:
            # logger.warning("Failed to retrieve gpu graphics processes", exc_info=True)
            return []


class AllGPUDevices:
    device_count: int
    devices: List[GPUDevice]
    
    def __init__(self) -> None:
        gpu_details_available = is_gpu_details_available()
        if gpu_details_available:
            logger.debug("GPU available. Starting setup")
        else:
            logger.error("There is no GPU available")
        self.devices = []

        if PYNVML_AVAILABLE:
            logger.debug("PyNVML available. Starting setup")
            pynvml.nvmlInit()
            nvidia_devices_count = pynvml.nvmlDeviceGetCount()
            for i in range(nvidia_devices_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                nvidia_gpu_device = NvidiaGPUDevice(handle=handle, gpu_index=i)
                self.devices.append(nvidia_gpu_device)

        if AMDSMI_AVAILABLE:
            logger.debug("AMDSMI available. Starting setup")
            try:
                amdsmi.amdsmi_init()
                amd_devices_handles = amdsmi.amdsmi_get_processor_handles()
                if len(amd_devices_handles) == 0:
                    print(
                        "No AMD GPUs foundon machine with amdsmi_get_processor_handles() !"
                    )
                else:
                    for i, handle in enumerate(amd_devices_handles):
                        # Try to get the actual device index from BDF (Bus/Device/Function)
                        # If this fails, fall back to enumeration index
                        try:
                            bdf_info = amdsmi.amdsmi_get_gpu_device_bdf(handle)
                            # BDF typically contains domain, bus, device, function
                            # The device portion often corresponds to the GPU index
                            # For now, we'll use the enumeration index but log the BDF
                            logger.debug(
                                f"Found AMD GPU device with handle {handle}, enum_index {i}, BDF {bdf_info}: {amdsmi.amdsmi_get_gpu_device_uuid(handle)}"
                            )
                            # Use enumerate index for now - this will be the index in the filtered list
                            gpu_index = i
                        except Exception:
                            logger.debug(
                                f"Found AMD GPU device with handle {handle} and index {i} : {amdsmi.amdsmi_get_gpu_device_uuid(handle)}"
                            )
                            gpu_index = i

                        amd_gpu_device = AMDGPUDevice(
                            handle=handle, gpu_index=gpu_index
                        )
                        self.devices.append(amd_gpu_device)
            except amdsmi.AmdSmiException as e:
                logger.warning(f"Failed to initialize AMDSMI: {e}", exc_info=True)
        self.device_count = len(self.devices)

    def get_gpu_static_info(self) -> List:
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

    def get_gpu_details(self) -> List:
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
                gpu_device = self.devices[i]
                devices_info.append(gpu_device.get_gpu_details())
            return devices_info

        except Exception:
            logger.warning("Failed to retrieve gpu information", exc_info=True)
            return []

    def get_delta(self, last_duration: Time) -> List:
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
                gpu_device = self.devices[i]
                devices_info.append(gpu_device.delta(last_duration))
            return devices_info

        except Exception:
            logger.warning("Failed to retrieve gpu information", exc_info=True)
            return []


def is_gpu_details_available() -> bool:
    """Returns True if the GPU details are available."""
    return PYNVML_AVAILABLE or AMDSMI_AVAILABLE
