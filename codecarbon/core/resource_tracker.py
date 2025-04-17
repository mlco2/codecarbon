from collections import Counter
from typing import List, Union

from codecarbon.core import cpu, gpu, powermetrics
from codecarbon.core.config import parse_gpu_ids
from codecarbon.core.util import detect_cpu_model, is_linux_os, is_mac_os, is_windows_os
from codecarbon.external.hardware import CPU, GPU, MODE_CPU_LOAD, AppleSiliconChip
from codecarbon.external.logger import logger
from codecarbon.external.ram import RAM


class ResourceTracker:
    cpu_tracker = gpu_tracker = ram_tracker = "Unspecified"

    def __init__(self, tracker):
        self.tracker = tracker

    def set_RAM_tracking(self):
        logger.info("[setup] RAM Tracking...")
        if self.tracker._force_ram_power is not None:
            self.ram_tracker = (
                f"User specified constant: {self.tracker._force_ram_power} Watts"
            )
            logger.info(
                f"Using user-provided RAM power: {self.tracker._force_ram_power} Watts"
            )
        else:
            self.ram_tracker = "RAM power estimation model"
        ram = RAM(
            tracking_mode=self.tracker._tracking_mode,
            force_ram_power=self.tracker._force_ram_power,
        )
        self.tracker._conf["ram_total_size"] = ram.machine_memory_GB
        self.tracker._hardware: List[Union[RAM, CPU, GPU, AppleSiliconChip]] = [ram]

    def set_CPU_tracking(self):
        logger.info("[setup] CPU Tracking...")
        cpu_number = self.tracker._conf.get("cpu_physical_count")
        tdp = cpu.TDP()
        if self.tracker._force_cpu_power is not None:
            logger.info(
                f"Using user-provided CPU power: {self.tracker._force_cpu_power} Watts"
            )
            self.cpu_tracker = "User Input TDP constant"
            max_power = self.tracker._force_cpu_power
        else:
            max_power = tdp.tdp * cpu_number if tdp.tdp is not None else None
        if self.tracker._conf.get("force_mode_cpu_load", False) and (
            tdp.tdp is not None or self.tracker._force_cpu_power is not None
        ):
            if cpu.is_psutil_available():
                # Register a CPU with MODE_CPU_LOAD
                model = tdp.model
                hardware_cpu = CPU.from_utils(
                    self.tracker._output_dir,
                    MODE_CPU_LOAD,
                    model,
                    max_power,
                    tracking_mode=self.tracker._tracking_mode,
                )
                self.cpu_tracker = MODE_CPU_LOAD
                self.tracker._conf["cpu_model"] = hardware_cpu.get_model()
                self.tracker._hardware.append(hardware_cpu)
                return
            else:
                logger.warning(
                    "Force CPU load mode requested but psutil is not available."
                )
        if cpu.is_powergadget_available() and self.tracker._force_cpu_power is None:
            logger.info("Tracking Intel CPU via Power Gadget")
            self.cpu_tracker = "Power Gadget"
            hardware_cpu = CPU.from_utils(
                self.tracker._output_dir, "intel_power_gadget"
            )
            self.tracker._hardware.append(hardware_cpu)
            self.tracker._conf["cpu_model"] = hardware_cpu.get_model()
        elif cpu.is_rapl_available():
            logger.info("Tracking Intel CPU via RAPL interface")
            self.cpu_tracker = "RAPL"
            hardware_cpu = CPU.from_utils(
                output_dir=self.tracker._output_dir, mode="intel_rapl"
            )
            self.tracker._hardware.append(hardware_cpu)
            self.tracker._conf["cpu_model"] = hardware_cpu.get_model()
            if "AMD Ryzen Threadripper" in self.tracker._conf["cpu_model"]:
                logger.warning(
                    "The RAPL energy and power reported is divided by 2 for all 'AMD Ryzen Threadripper' as it seems to give better results."
                )
        # change code to check if powermetrics needs to be installed or just sudo setup
        elif (
            powermetrics.is_powermetrics_available()
            and self.tracker._force_cpu_power is None
        ):
            logger.info("Tracking Apple CPU and GPU via PowerMetrics")
            self.gpu_tracker = "PowerMetrics"
            self.cpu_tracker = "PowerMetrics"
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
                if (
                    "M1" in detect_cpu_model()
                    or "M2" in detect_cpu_model()
                    or "M3" in detect_cpu_model()
                ):
                    cpu_tracking_install_instructions = ""
                    cpu_tracking_install_instructions = "Mac OS and ARM processor detected: Please enable PowerMetrics sudo to measure CPU"
                else:
                    cpu_tracking_install_instructions = "Mac OS detected: Please install Intel Power Gadget or enable PowerMetrics sudo to measure CPU"
            elif is_windows_os():
                cpu_tracking_install_instructions = "Windows OS detected: Please install Intel Power Gadget to measure CPU"
            elif is_linux_os():
                cpu_tracking_install_instructions = "Linux OS detected: Please ensure RAPL files exist at /sys/class/powercap/intel-rapl/subsystem to measure CPU"
            logger.warning(
                f"No CPU tracking mode found. Falling back on estimation based on TDP for CPU. \n {cpu_tracking_install_instructions}\n"
            )
            self.cpu_tracker = "TDP constant"
            model = tdp.model
            if (max_power is None) and self.tracker._force_cpu_power:
                # We haven't been able to calculate CPU power but user has input a default one. We use it
                user_input_power = self.tracker._force_cpu_power
                logger.debug(f"Using user input TDP: {user_input_power} W")
                self.cpu_tracker = "User Input TDP constant"
                max_power = user_input_power
            logger.info(f"CPU Model on constant consumption mode: {model}")
            self.tracker._conf["cpu_model"] = model
            if tdp:
                if cpu.is_psutil_available():
                    logger.warning(
                        "No CPU tracking mode found. Falling back on CPU load mode."
                    )
                    hardware_cpu = CPU.from_utils(
                        self.tracker._output_dir,
                        MODE_CPU_LOAD,
                        model,
                        max_power,
                        tracking_mode=self.tracker._tracking_mode,
                    )
                    self.cpu_tracker = MODE_CPU_LOAD
                else:
                    logger.warning(
                        "No CPU tracking mode found. Falling back on CPU constant mode."
                    )
                    hardware_cpu = CPU.from_utils(
                        self.tracker._output_dir, "constant", model, max_power
                    )
                    self.cpu_tracker = "global constant"
                self.tracker._hardware.append(hardware_cpu)
            else:
                if cpu.is_psutil_available():
                    logger.warning(
                        "Failed to match CPU TDP constant. Falling back on CPU load mode."
                    )
                    hardware_cpu = CPU.from_utils(
                        self.tracker._output_dir,
                        MODE_CPU_LOAD,
                        model,
                        max_power,
                        tracking_mode=self.tracker._tracking_mode,
                    )
                    self.cpu_tracker = MODE_CPU_LOAD
                else:
                    logger.warning(
                        "Failed to match CPU TDP constant. Falling back on a global constant."
                    )
                    self.cpu_tracker = "global constant"
                    hardware_cpu = CPU.from_utils(self.tracker._output_dir, "constant")
                self.tracker._hardware.append(hardware_cpu)

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
            self.gpu_tracker = "pynvml"
        else:
            logger.info("No GPU found.")

    def set_CPU_GPU_ram_tracking(self):
        """
        Set up CPU, GPU and RAM tracking based on the user's configuration.
        param tracker: BaseEmissionsTracker object
        """
        self.set_RAM_tracking()
        self.set_CPU_tracking()
        self.set_GPU_tracking()

        logger.info(
            f"""The below tracking methods have been set up:
                RAM Tracking Method: {self.ram_tracker}
                CPU Tracking Method: {self.cpu_tracker}
                GPU Tracking Method: {self.gpu_tracker}
            """
        )
