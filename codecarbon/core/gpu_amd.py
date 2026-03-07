import subprocess
from collections import namedtuple
from typing import Callable

from codecarbon.core.gpu_device import GPUDevice
from codecarbon.external.logger import logger


def is_rocm_system():
    """Returns True if the system has an rocm-smi interface."""
    try:
        # Check if rocm-smi is available
        subprocess.check_output(["rocm-smi", "--help"])
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


try:
    import amdsmi

    AMDSMI_AVAILABLE = True
except ImportError:
    amdsmi = None
    if is_rocm_system():
        logger.warning(
            "AMD GPU detected but amdsmi is not available. "
            "Please install amdsmi to get GPU metrics."
        )
    AMDSMI_AVAILABLE = False
except AttributeError as e:
    amdsmi = None
    # In some environments, amdsmi may be present but not properly configured, leading to AttributeError when importing
    logger.warning(
        "AMD GPU detected but amdsmi is not properly configured. "
        "Please ensure amdsmi is correctly installed to get GPU metrics."
        "Tips : check consistency between Python amdsmi package and ROCm versions, and ensure AMD drivers are up to date."
        f" Error: {e}"
    )
    AMDSMI_AVAILABLE = False


class AMDGPUDevice(GPUDevice):
    _dual_gcd_warning_emitted = False

    def _is_dual_gcd_power_limited_model(self, gpu_name: str) -> bool:
        name = gpu_name.upper()
        # Dual-GCD models: MI2xx (except MI210) and MI3xx series
        if "MI210" in name:
            return False
        return "MI2" in name or "MI3" in name

    def _init_static_details(self) -> None:
        super()._init_static_details()

        self._known_zero_energy_counter = self._is_dual_gcd_power_limited_model(
            self._gpu_name
        )

    def emit_selection_warning(self) -> None:
        if not self._known_zero_energy_counter:
            return

        if not self.__class__._dual_gcd_warning_emitted:
            logger.warning(
                "Detected AMD Instinct MI250/MI250X/MI300X/MI300A family GPU. "
                "These dual-GCD devices report power on one GCD while the other reports zero."
            )
            self.__class__._dual_gcd_warning_emitted = True

        if self.gpu_index % 2 == 1:
            logger.warning(
                f"GPU {self._gpu_name} with index {self.gpu_index} is expected to report zero energy consumption due to being the second GCD in a dual-GCD configuration."
            )
        else:
            logger.warning(
                f"GPU {self._gpu_name} with index {self.gpu_index} is expected to report both GCDs' energy consumption as it is the first GCD in a dual-GCD configuration."
            )

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
            energy_key = None
            if "energy_accumulator" in energy_count:
                energy_key = "energy_accumulator"
            elif "power" in energy_count:
                energy_key = "power"
            if energy_key is None:
                logger.warning(
                    f"Neither 'energy_accumulator' nor 'power' found in energy_count: {energy_count}"
                )
                return None
            # The amdsmi library returns a dict with energy counter and resolution
            # The counter is the actual accumulated value, resolution tells us how much each unit is worth
            counter_value = energy_count.get(energy_key, 0)
            counter_resolution_uj = energy_count.get("counter_resolution", 0)
            if counter_value == 0 and counter_resolution_uj > 0:
                # In some cases, the energy_accumulator is 0 but it exist in the metrics info, try to get it from there as a fallback
                metrics_info = self._get_gpu_metrics_info()
                counter_value = metrics_info.get(energy_key, 0)
                if counter_value == 0:
                    if getattr(self, "_known_zero_energy_counter", False):
                        return 0
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
        try:
            # amdsmi_get_temp_metric returns temperature in millidegrees Celsius
            temp_milli_celsius = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_temp_metric,
                self.handle,
                sensor_type=amdsmi.AmdSmiTemperatureType.HOTSPOT,
                metric=amdsmi.AmdSmiTemperatureMetric.CURRENT,
            )
            # Convert from millidegrees to degrees
            temp = temp_milli_celsius // 1000
            # In some cases, the hotspot temperature can be 0 or not available, try to get it from metrics info as a fallback
            if temp == 0:
                metrics_info = self._get_gpu_metrics_info()
                temp_celsius = metrics_info.get("temperature_hotspot", 0)
                temp = temp_celsius
        except amdsmi.amdsmi_exception.AmdSmiLibraryException as e:
            logger.debug(f"Failed to retrieve gpu temperature: {e}")
            temp = 0

        return temp

    def _get_power_usage(self):
        """Returns power usage in Watts"""
        power_info = self._call_amdsmi_with_reinit(
            amdsmi.amdsmi_get_power_info, self.handle
        )

        try:
            power = int(power_info.get("average_socket_power", 0))
        except (ValueError, TypeError):
            power = 0

        if power == 0:
            # In some cases, the average_socket_power can be 0 or not available, try to get it from metrics info as a fallback
            try:
                metrics_info = self._get_gpu_metrics_info()
                power = int(metrics_info.get("average_socket_power", 0))
            except (ValueError, TypeError):
                power = 0

        return power

    def _get_power_limit(self):
        """Returns max power usage in Watts"""
        # Get power cap info which contains power_cap in uW (microwatts)
        try:
            power_cap_info = self._call_amdsmi_with_reinit(
                amdsmi.amdsmi_get_power_cap_info, self.handle
            )
            # power_cap is in uW, convert to W
            return int(power_cap_info["power_cap"] / 1_000_000)
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
