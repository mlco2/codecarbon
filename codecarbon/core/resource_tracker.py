from collections import Counter
from typing import List, Union

from codecarbon.core import cpu, gpu, macmon, powermetrics
from codecarbon.core.config import parse_gpu_ids
from codecarbon.core.util import detect_cpu_model, is_linux_os, is_mac_os, is_windows_os
from codecarbon.external.hardware import CPU, GPU, RAM, AppleSiliconChip
from codecarbon.external.logger import logger


class ResourceTracker:
    cpu_tracker = gpu_tracker = ram_tracker = "Unspecified"

    def __init__(self, tracker):
        self.tracker = tracker

    def set_RAM_tracking(self):
        logger.info("[setup] RAM Tracking...")
        self.ram_tracker = "3 Watts for 8 GB ratio constant"
        ram = RAM(tracking_mode=self.tracker._tracking_mode)
        self.tracker._conf["ram_total_size"] = ram.machine_memory_GB
        self.tracker._hardware: List[Union[RAM, CPU, GPU, AppleSiliconChip]] = [ram]

    def set_CPU_tracking(self):
        logger.info("[setup] CPU Tracking...")
        if cpu.is_powergadget_available() and self.tracker._default_cpu_power is None:
            logger.info("Tracking Intel CPU via Power Gadget")
            self.cpu_tracker = "Power Gadget"
            hardware = CPU.from_utils(self.tracker._output_dir, "intel_power_gadget")
            self.tracker._hardware.append(hardware)
            self.tracker._conf["cpu_model"] = hardware.get_model()
        elif cpu.is_rapl_available():
            logger.info("Tracking Intel CPU via RAPL interface")
            self.cpu_tracker = "RAPL"
            hardware = CPU.from_utils(self.tracker._output_dir, "intel_rapl")
            self.tracker._hardware.append(hardware)
            self.tracker._conf["cpu_model"] = hardware.get_model()
        # change code to check if powermetrics needs to be installed or just sudo setup
        elif self.tracker._default_cpu_power is None:
            if macmon.is_macmon_available():
                self.gpu_tracker = "MacMon"
                self.cpu_tracker = "MacMon"
            elif powermetrics.is_powermetrics_available():
                self.cpu_tracker = "PowerMetrics"
                self.gpu_tracker = "PowerMetrics"
            logger.info(f"Tracking Apple CPU and GPU using {self.cpu_tracker}")
            hardware_cpu = AppleSiliconChip.from_utils(
                self.tracker._output_dir, chip_part="CPU"
            )
            self.tracker._hardware.append(hardware_cpu)
            self.tracker._conf["cpu_model"] = hardware_cpu.get_model()

            hardware_gpu = AppleSiliconChip.from_utils(
                self.tracker._output_dir, chip_part="GPU"
            )
            self.tracker._hardware.append(hardware_gpu)

            self.tracker._conf["gpu_model"] = hardware_gpu.get_model()
            self.tracker._conf["gpu_count"] = 1
        else:
            # Explain what to install to increase accuracy
            cpu_tracking_install_instructions = ""
            if is_mac_os():
                if any((m in detect_cpu_model() for m in ["M1", "M2", "M3", "M4"])):
                    cpu_tracking_install_instructions = ""
                    cpu_tracking_install_instructions = "Mac OS and ARM processor detected: Please enable PowerMetrics sudo to measure CPU"
                else:
                    cpu_tracking_install_instructions = "Mac OS detected: Please install Intel Power Gadget or enable PowerMetrics sudo to measure CPU"
            elif is_windows_os():
                cpu_tracking_install_instructions = "Windows OS detected: Please install Intel Power Gadget to measure CPU"
            elif is_linux_os():
                cpu_tracking_install_instructions = "Linux OS detected: Please ensure RAPL files exist at \\sys\\class\\powercap\\intel-rapl to measure CPU"
            logger.warning(
                f"No CPU tracking mode found. Falling back on CPU constant mode. \n {cpu_tracking_install_instructions}\n"
            )
            self.cpu_tracker = "TDP constant"
            tdp = cpu.TDP()
            power = tdp.tdp
            model = tdp.model
            if (power is None) and self.tracker._default_cpu_power:
                # We haven't been able to calculate CPU power but user has input a default one. We use it
                user_input_power = self.tracker._default_cpu_power
                logger.debug(f"Using user input TDP: {user_input_power} W")
                self.cpu_tracker = "User Input TDP constant"
                power = user_input_power
            logger.info(f"CPU Model on constant consumption mode: {model}")
            self.tracker._conf["cpu_model"] = model
            if tdp:
                hardware = CPU.from_utils(
                    self.tracker._output_dir, "constant", model, power
                )
                self.tracker._hardware.append(hardware)
            else:
                logger.warning(
                    "Failed to match CPU TDP constant. "
                    + "Falling back on a global constant."
                )
                self.cpu_tracker = "global constant"
                hardware = CPU.from_utils(self.tracker._output_dir, "constant")
                self.tracker._hardware.append(hardware)

    def set_GPU_tracking(self):
        logger.info("[setup] GPU Tracking...")
        if self.tracker._gpu_ids:
            # If _gpu_ids is a string or a list of int, parse it to a list of ints
            if isinstance(self.tracker._gpu_ids, str) or (
                isinstance(self.tracker._gpu_ids, list)
                and all(isinstance(gpu_id, int) for gpu_id in self.tracker._gpu_ids)
            ):
                self.tracker._gpu_ids: List[int] = parse_gpu_ids(self.tracker._gpu_ids)
                self.tracker._conf["gpu_ids"] = self.tracker._gpu_ids
                self.tracker._conf["gpu_count"] = len(self.tracker._gpu_ids)
            else:
                logger.warning(
                    "Invalid gpu_ids format. Expected a string or a list of ints."
                )
        if gpu.is_gpu_details_available():
            logger.info("Tracking Nvidia GPU via pynvml")
            gpu_devices = GPU.from_utils(self.tracker._gpu_ids)
            self.tracker._hardware.append(gpu_devices)
            gpu_names = [n["name"] for n in gpu_devices.devices.get_gpu_static_info()]
            gpu_names_dict = Counter(gpu_names)
            self.tracker._conf["gpu_model"] = "".join(
                [f"{i} x {name}" for name, i in gpu_names_dict.items()]
            )
            if self.tracker._conf.get("gpu_count") is None:
                self.tracker._conf["gpu_count"] = len(
                    gpu_devices.devices.get_gpu_static_info()
                )
        else:
            logger.info("No GPU found.")

    def set_CPU_GPU_ram_tracking(self):
        self.set_RAM_tracking()
        self.set_CPU_tracking()
        self.set_GPU_tracking()

        logger.debug(
            f"""The below tracking methods have been set up:
                RAM Tracking Method: {self.ram_tracker}
                CPU Tracking Method: {self.cpu_tracker}
                GPU Tracking Method: {self.gpu_tracker}
            """
        )
