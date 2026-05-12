"""
Implements tracking for AWS Inferentia and Inferentia2 AI accelerator chips
via the Neuron sysfs interface.

Sysfs power file location:
/sys/devices/virtual/neuron_device/neuron{i}/stats/power/utilization

Sysfs power file format:
<status>,<timestamp>,<min_power>,<max_power>,<avg_power>

Where power values are percentages (0.00-100.00) of max TDP.
Updated every 60 seconds by the Neuron driver.

IMPORTANT - Sampling frequency limitation:
The Neuron sysfs power file updates every 60 seconds.
codecarbon reads it every 15 seconds by default, meaning
the same value may be read up to 4 times between updates.

Impact:
- Steady workloads: minimal impact, power is relatively constant
- Bursty workloads: may miss power spikes between updates
- Runs < 60 seconds: energy estimate may be based on a single sample
- Long runs: averages out over time, impact diminishes

NOTE: Power is reported at device level, not per-process.
Accurate for exclusive instances, approximate for shared Neuron cores.
"""

import glob
import os
from typing import Dict, List, Optional, Tuple

from codecarbon.external.logger import logger

# Maximum TDP per device type in watts.
# Only Inferentia (inf1) and Inferentia2 (inf2) are currently supported.
# Add other devices when their power specs are properly researched.
# TDP values are approximate and used to estimate watts from utilization%.
NEURON_DEVICE_TDP_WATTS = {
    # long format from device_name sysfs file
    "inferentia": 75,
    "inferentia2": 100,
    # shorthand format from instance_type sysfs file
    "inf1": 75,
    "inf2": 100,
}


def is_neuron_system() -> bool:
    """
    Check if AWS Inferentia/Inferentia2 Neuron device is available
    by checking if the Neuron sysfs directory exists.
    Returns True if Neuron devices are present, False otherwise.
    """
    return os.path.exists("/sys/devices/virtual/neuron_device")


class NeuronDevice:
    """
    Represents a single AWS Inferentia/Inferentia2 Neuron device.

    Reads power utilization from Neuron sysfs at:
    /sys/devices/virtual/neuron_device/neuron{i}/stats/power/utilization

    Power is reported as a percentage of max TDP, updated every 60 seconds.
    Watts are estimated by multiplying utilization% by the device TDP.

    Accuracy limitations:
    - Power derived from utilization% x TDP, not directly measured
    - sysfs updates every 60 seconds, codecarbon reads every 15 seconds
    - Device-level power only, not per-process attribution
    - TDP values are approximate, not officially confirmed by AWS
      for power tracking purposes
    """

    def __init__(self, device_path: str, device_index: int):
        self._device_path = device_path
        self._device_index = device_index
        self._max_power_watts = self._get_max_power_watts()

    def _get_max_power_watts(self) -> float:
        """
        Look up device TDP by reading device_name, instance_type,
        or arch_type from the sysfs info directory.
        Tries each file in order, returns first match.
        Returns 0.0 if device is not supported or file cannot be read.
        """
        try:
            for filename in ["device_name", "instance_type", "arch_type"]:
                path = os.path.join(self._device_path, "info", "architecture", filename)
                if not os.path.exists(path):
                    continue
                with open(path, "r") as f:
                    name = f.read().strip().lower()
                tdp = NEURON_DEVICE_TDP_WATTS.get(name, 0.0)
                if tdp > 0:
                    logger.debug(
                        f"NeuronDevice {self._device_index}: "
                        f"{filename}='{name}', TDP={tdp}W"
                    )
                    return tdp
                else:
                    logger.warning(
                        f"NeuronDevice {self._device_index}: "
                        f"device '{name}' is not currently supported. "
                        "Only Inferentia (inf1) and Inferentia2 (inf2) "
                        "are supported. Power will be reported as 0.0W."
                    )
                    return 0.0
            logger.warning(
                f"NeuronDevice {self._device_index}: "
                "could not determine device type from sysfs info directory."
            )
            return 0.0
        except Exception as e:
            logger.debug(
                f"NeuronDevice {self._device_index}: "
                f"could not read device info: {e}"
            )
            return 0.0

    def _read_power_file(self) -> Optional[Tuple[str, float, float, float]]:
        """
        Read and parse the Neuron sysfs power utilization file.

        Format: <status>,<timestamp>,<min_power>,<max_power>,<avg_power>

        Returns (status, min_pct, max_pct, avg_pct) or None on error.
        """
        try:
            power_file = os.path.join(
                self._device_path, "stats", "power", "utilization"
            )
            if not os.path.exists(power_file):
                logger.debug(
                    f"NeuronDevice {self._device_index}: "
                    f"power file not found at {power_file}"
                )
                return None

            with open(power_file, "r") as f:
                content = f.read().strip()

            parts = content.split(",")
            if len(parts) != 5:
                logger.debug(
                    f"NeuronDevice {self._device_index}: "
                    f"unexpected power file format: {content}"
                )
                return None

            status, _, min_pct, max_pct, avg_pct = parts
            return status, float(min_pct), float(max_pct), float(avg_pct)

        except Exception as e:
            logger.debug(
                f"NeuronDevice {self._device_index}: " f"could not read power file: {e}"
            )
            return None

    def get_utilization_pct(self) -> float:
        """
        Returns the raw average power utilization percentage (0.00-100.00)
        as reported directly by the Neuron sysfs interface.
        This is the direct measured value with no estimation involved.
        Returns 0.0 if status is not POWER_STATUS_VALID or on error.
        """
        result = self._read_power_file()
        if result is None:
            return 0.0

        status, _, _, avg_pct = result

        if status != "POWER_STATUS_VALID":
            logger.debug(
                f"NeuronDevice {self._device_index}: "
                f"power status: {status}, returning 0.0%"
            )
            return 0.0

        logger.debug(
            f"NeuronDevice {self._device_index}: " f"utilization={avg_pct:.2f}%"
        )
        return avg_pct

    def get_power_watts(self) -> float:
        """
        Returns estimated power in watts by multiplying utilization%
        by the device TDP.

        NOTE: This is an estimation. For the raw measured value
        use get_utilization_pct() instead.
        Returns 0.0 if TDP is unknown or status is not POWER_STATUS_VALID.
        """
        if self._max_power_watts == 0.0:
            logger.debug(
                f"NeuronDevice {self._device_index}: "
                "TDP unknown, cannot estimate watts"
            )
            return 0.0

        result = self._read_power_file()
        if result is None:
            return 0.0

        status, _, _, avg_pct = result

        if status != "POWER_STATUS_VALID":
            logger.debug(
                f"NeuronDevice {self._device_index}: "
                f"power status: {status}, returning 0.0W"
            )
            return 0.0

        watts = (avg_pct / 100.0) * self._max_power_watts
        logger.debug(
            f"NeuronDevice {self._device_index}: "
            f"avg={avg_pct:.2f}%, TDP={self._max_power_watts}W "
            f"=> {watts:.2f}W"
        )
        return watts

    def get_device_index(self) -> int:
        return self._device_index


class AllNeuronDevices:
    """
    Discovers and manages all AWS Inferentia/Inferentia2 Neuron devices
    on the system by scanning the Neuron sysfs directory.
    """

    def __init__(self):
        self._devices: List[NeuronDevice] = self._discover_devices()
        logger.info(f"Found {len(self._devices)} Neuron device(s)")

    def _discover_devices(self) -> List[NeuronDevice]:
        """
        Scan sysfs for Neuron devices and return a sorted list
        of NeuronDevice objects.
        Uses neuron[0-9]* glob to avoid matching neuron_core directories.
        """
        base_path = "/sys/devices/virtual/neuron_device"
        device_paths = sorted(glob.glob(os.path.join(base_path, "neuron[0-9]*")))
        devices = []
        for i, path in enumerate(device_paths):
            if os.path.isdir(path):
                devices.append(NeuronDevice(path, i))
                logger.info(f"Neuron device {i} found at {path}")
        return devices

    @property
    def device_count(self) -> int:
        return len(self._devices)

    def get_total_power_watts(self) -> float:
        """
        Sum estimated power in watts across all Neuron devices.
        See NeuronDevice.get_power_watts() for accuracy limitations.
        """
        return sum(d.get_power_watts() for d in self._devices)

    def get_total_utilization_pct(self) -> float:
        """
        Average raw utilization percentage across all Neuron devices.
        This is the direct measured value with no estimation involved.
        Returns 0.0 if no devices are present.
        """
        if not self._devices:
            return 0.0
        return sum(d.get_utilization_pct() for d in self._devices) / len(self._devices)

    def get_device_details(self) -> List[Dict]:
        """
        Return a list of dicts with per-device power and utilization.
        """
        return [
            {
                "device_index": d.get_device_index(),
                "power_watts": d.get_power_watts(),
                "utilization_pct": d.get_utilization_pct(),
            }
            for d in self._devices
        ]
