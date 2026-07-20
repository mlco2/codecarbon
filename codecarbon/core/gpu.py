from typing import List

from codecarbon.core import gpu_amd, gpu_nvidia
from codecarbon.core.gpu_device import GPUDevice
from codecarbon.core.units import Time
from codecarbon.external.logger import logger

AMDSMI_AVAILABLE = gpu_amd.AMDSMI_AVAILABLE
PYNVML_AVAILABLE = gpu_nvidia.PYNVML_AVAILABLE

AMDGPUDevice = gpu_amd.AMDGPUDevice
NvidiaGPUDevice = gpu_nvidia.NvidiaGPUDevice
is_rocm_system = gpu_amd.is_rocm_system
is_nvidia_system = gpu_nvidia.is_nvidia_system

# Backward-compatible module attributes
amdsmi = gpu_amd.amdsmi
pynvml = gpu_nvidia.pynvml


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
            gpu_nvidia.pynvml.nvmlInit()
            nvidia_devices_count = gpu_nvidia.pynvml.nvmlDeviceGetCount()
            for i in range(nvidia_devices_count):
                handle = gpu_nvidia.pynvml.nvmlDeviceGetHandleByIndex(i)
                nvidia_gpu_device = NvidiaGPUDevice(handle=handle, gpu_index=i)
                self.devices.append(nvidia_gpu_device)

        if AMDSMI_AVAILABLE:
            logger.debug("AMDSMI available. Starting setup")
            try:
                gpu_amd.amdsmi.amdsmi_init()
                amd_devices_handles = gpu_amd.amdsmi.amdsmi_get_processor_handles()
                if len(amd_devices_handles) == 0:
                    logger.warning(
                        "No AMD GPUs found on machine with amdsmi_get_processor_handles() !"
                    )
                else:
                    for i, handle in enumerate(amd_devices_handles):
                        # Try to get the actual device index from BDF (Bus/Device/Function)
                        # If this fails, fall back to enumeration index
                        try:
                            bdf_info = gpu_amd.amdsmi.amdsmi_get_gpu_device_bdf(handle)
                            # BDF typically contains domain, bus, device, function
                            # The device portion often corresponds to the GPU index
                            # For now, we'll use the enumeration index but log the BDF
                            logger.debug(
                                f"Found AMD GPU device with handle {handle}, enum_index {i}, BDF {bdf_info}: {gpu_amd.amdsmi.amdsmi_get_gpu_device_uuid(handle)}"
                            )
                            # Use enumerate index for now - this will be the index in the filtered list
                            gpu_index = i
                        except Exception:
                            logger.debug(
                                f"Found AMD GPU device with handle {handle} and index {i} : {gpu_amd.amdsmi.amdsmi_get_gpu_device_uuid(handle)}"
                            )
                            gpu_index = i

                        amd_gpu_device = AMDGPUDevice(
                            handle=handle, gpu_index=gpu_index
                        )
                        self.devices.append(amd_gpu_device)
            except gpu_amd.amdsmi.AmdSmiException as e:
                logger.warning(f"Failed to initialize AMDSMI: {e}", exc_info=True)
        self.device_count = len(self.devices)

    def start(self) -> None:
        for device in self.devices:
            if hasattr(device, "start"):
                device.start()

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
