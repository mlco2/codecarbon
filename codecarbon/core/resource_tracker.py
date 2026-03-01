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

    def _setup_cpu_load_mode(self, tdp, max_power):
        """Set up CPU tracking in load mode using psutil."""
        if not cpu.is_psutil_available():
            logger.warning("Force CPU load mode requested but psutil is not available.")
            return False

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
        return True

    def _setup_power_gadget(self):
        """Set up CPU tracking using Intel Power Gadget."""
        logger.info("Tracking Intel CPU via Power Gadget")
        self.cpu_tracker = "Power Gadget"
        hardware_cpu = CPU.from_utils(self.tracker._output_dir, "intel_power_gadget")
        self.tracker._hardware.append(hardware_cpu)
        self.tracker._conf["cpu_model"] = hardware_cpu.get_model()
        return True

    def _setup_rapl(self):
        """Set up CPU tracking using RAPL interface."""
        logger.info("Tracking Intel CPU via RAPL interface")
        self.cpu_tracker = "RAPL"
        hardware_cpu = CPU.from_utils(
            output_dir=self.tracker._output_dir,
            mode="intel_rapl",
            rapl_include_dram=self.tracker._rapl_include_dram,
            rapl_prefer_psys=self.tracker._rapl_prefer_psys,
        )
        self.tracker._hardware.append(hardware_cpu)
        self.tracker._conf["cpu_model"] = hardware_cpu.get_model()
        return True

    def _setup_powermetrics(self):
        """Set up CPU and GPU tracking using PowerMetrics (Apple Silicon)."""
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
        return True

    def _get_install_instructions(self):
        """Get CPU tracking installation instructions for the current OS."""
        if is_mac_os():
            cpu_model = detect_cpu_model()
            if "M1" in cpu_model or "M2" in cpu_model or "M3" in cpu_model:
                return "Mac OS and ARM processor detected: Please enable PowerMetrics sudo to measure CPU"
            else:
                return "Mac OS detected: Please install Intel Power Gadget or enable PowerMetrics sudo to measure CPU"
        elif is_windows_os():
            return (
                "Windows OS detected: Please install Intel Power Gadget to measure CPU"
            )
        elif is_linux_os():
            return "Linux OS detected: Please ensure RAPL files exist, and are readable, at /sys/class/powercap/intel-rapl/subsystem to measure CPU"
        return ""

    def _setup_fallback_tracking(self, tdp, max_power):
        """Set up fallback CPU tracking using TDP estimation."""
        cpu_tracking_install_instructions = self._get_install_instructions()
        logger.warning(
            f"No CPU tracking mode found. Falling back on estimation based on TDP for CPU. \n {cpu_tracking_install_instructions}\n"
        )

        self.cpu_tracker = "TDP constant"
        model = tdp.model

        if (max_power is None) and self.tracker._force_cpu_power:
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

    def set_CPU_tracking(self):
        logger.info("[setup] CPU Tracking...")
        cpu_number = self.tracker._conf.get("cpu_physical_count")
        tdp = None
        max_power = None

        if self.tracker._force_cpu_power is not None:
            logger.info(
                f"Using user-provided CPU power: {self.tracker._force_cpu_power} Watts"
            )
            self.cpu_tracker = "User Input TDP constant"
            max_power = self.tracker._force_cpu_power

        # Try force CPU load mode if requested
        if self.tracker._conf.get("force_mode_cpu_load", False):
            if tdp is None:
                tdp = cpu.TDP()
            if max_power is None:
                max_power = tdp.tdp * cpu_number if tdp.tdp is not None else None
            if tdp.tdp is not None or self.tracker._force_cpu_power is not None:
                if self._setup_cpu_load_mode(tdp, max_power):
                    return

        # Try various tracking methods in order of preference
        if cpu.is_powergadget_available() and self.tracker._force_cpu_power is None:
            self._setup_power_gadget()
        elif cpu.is_rapl_available() and self.tracker._force_cpu_power is None:
            self._setup_rapl()
        elif (
            powermetrics.is_powermetrics_available()
            and self.tracker._force_cpu_power is None
        ):
            self._setup_powermetrics()
        else:
            if tdp is None:
                tdp = cpu.TDP()
            if max_power is None:
                max_power = tdp.tdp * cpu_number if tdp.tdp is not None else None
            self._setup_fallback_tracking(tdp, max_power)

    def set_GPU_tracking(self):
        logger.info("[setup] GPU Tracking...")
        if self.tracker._gpu_ids:
            self.tracker._gpu_ids = parse_gpu_ids(self.tracker._gpu_ids)
            if self.tracker._gpu_ids:
                self.tracker._conf["gpu_ids"] = self.tracker._gpu_ids
                self.tracker._conf["gpu_count"] = len(self.tracker._gpu_ids)

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
            self.tracker._conf.setdefault("gpu_count", 0)
            self.tracker._conf.setdefault("gpu_model", "")

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
