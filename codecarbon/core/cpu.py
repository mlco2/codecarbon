"""
Implements tracking Intel CPU Power Consumption on Mac and Windows
using Intel Power Gadget
https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html
"""

import os
import re
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple

import pandas as pd
import psutil
from rapidfuzz import fuzz, process, utils

from codecarbon.core.rapl import RAPLFile
from codecarbon.core.units import Time
from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger
from codecarbon.input import DataSource

# default W value per core for a CPU if no model is found in the ref csv
DEFAULT_POWER_PER_CORE = 4


def is_powergadget_available() -> bool:
    """
    Checks if Intel Power Gadget is available on the system.

    Returns:
        bool: `True` if Intel Power Gadget is available, `False` otherwise.
    """
    try:
        IntelPowerGadget()
        return True
    except Exception as e:
        logger.debug(
            "Not using PowerGadget, an exception occurred while instantiating "
            + "IntelPowerGadget : %s",
            e,
        )
        return False


def is_rapl_available() -> bool:
    """
    Checks if Intel RAPL is available on the system.

    Returns:
        bool: `True` if Intel RAPL is available, `False` otherwise.
    """
    try:
        IntelRAPL()
        return True
    except Exception as e:
        logger.debug(
            "Not using the RAPL interface, an exception occurred while instantiating "
            + "IntelRAPL : %s",
            e,
        )
        return False


def is_psutil_available():
    try:
        nice = psutil.cpu_times().nice
        if nice > 0.0001:
            return True
        else:
            logger.debug(
                f"is_psutil_available() : psutil.cpu_times().nice is too small : {nice} !"
            )
            return False
    except Exception as e:
        logger.debug(
            "Not using the psutil interface, an exception occurred while instantiating "
            + f"psutil.cpu_times : {e}",
        )
        return False


class IntelPowerGadget:
    """
    A class to interface with Intel Power Gadget for monitoring CPU power consumption on Windows and (non-Apple Silicon) macOS.

    This class provides methods to set up and execute Intel Power Gadget's command-line interface (CLI) to
    log power consumption data over a specified duration and resolution. It also includes functionality to
    read and process the logged data to extract CPU power details.

    Methods:
        start():
            Placeholder method for starting the Intel Power Gadget monitoring.

        get_cpu_details() -> Dict:
            Fetches the CPU power details by reading the values from the logged CSV file.

    """

    _osx_exec = "PowerLog"
    _osx_exec_backup = "/Applications/Intel Power Gadget/PowerLog"
    _windows_exec = "PowerLog3.0.exe"

    def __init__(
        self,
        output_dir: str = ".",
        duration=1,
        resolution=100,
        log_file_name="intel_power_gadget_log.csv",
    ):
        self._log_file_path = os.path.join(output_dir, log_file_name)
        self._system = sys.platform.lower()
        self._duration = duration
        self._resolution = resolution
        self._windows_exec_backup = None
        self._setup_cli()

    def _setup_cli(self) -> None:
        """
        Setup cli command to run Intel Power Gadget
        """
        if self._system.startswith("win"):
            self._get_windows_exec_backup()
            if shutil.which(self._windows_exec):
                self._cli = shutil.which(
                    self._windows_exec
                )  # Windows exec is a relative path
            elif shutil.which(self._windows_exec_backup):
                self._cli = self._windows_exec_backup
            else:
                raise FileNotFoundError(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        elif self._system.startswith("darwin"):
            if shutil.which(self._osx_exec):
                self._cli = self._osx_exec
            elif shutil.which(self._osx_exec_backup):
                self._cli = self._osx_exec_backup
            else:
                raise FileNotFoundError(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        else:
            raise SystemError("Platform not supported by Intel Power Gadget")

    def _get_windows_exec_backup(self) -> None:
        """
        Find the windows executable for the current version of intel power gadget.
        Example: "C:\\Program Files\\Intel\\Power Gadget 3.5\\PowerLog3.0.exe"
        """
        parent_folder = "C:\\Program Files\\Intel\\"

        # Get a list of all subdirectories in the parent folder
        subfolders = [f.name for f in os.scandir(parent_folder) if f.is_dir()]

        # Look for a folder that contains "Power Gadget" in its name
        desired_folder = next(
            (folder for folder in subfolders if "Power Gadget" in folder), None
        )
        if desired_folder:
            self._windows_exec_backup = os.path.join(
                parent_folder, desired_folder, self._windows_exec
            )
        else:
            self._windows_exec_backup = None

    def _log_values(self) -> None:
        """
        Logs output from Intel Power Gadget command line to a file
        """
        returncode = None
        if self._system.startswith("win"):
            returncode = subprocess.call(
                [
                    self._cli,
                    "-duration",
                    str(self._duration),
                    "-resolution",
                    str(self._resolution),
                    "-file",
                    self._log_file_path,
                ],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        elif self._system.startswith("darwin"):
            returncode = subprocess.call(
                f"'{self._cli}' -duration {self._duration} -resolution {self._resolution} -file {self._log_file_path} > /dev/null",  # noqa: E501
                shell=True,
            )
        else:
            return None

        if returncode != 0:
            logger.warning(
                "Returncode while logging power values using "
                + "Intel Power Gadget: %s",
                returncode,
            )

    def get_cpu_details(self) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from a logged csv file
        in _log_values function
        """
        self._log_values()
        cpu_details = {}
        try:
            cpu_data = pd.read_csv(self._log_file_path).dropna()
            for col_name in cpu_data.columns:
                if col_name in ["System Time", "Elapsed Time (sec)", "RDTSC"]:
                    continue
                if "Cumulative" in col_name:
                    cpu_details[col_name] = cpu_data[col_name].iloc[-1]
                else:
                    cpu_details[col_name] = cpu_data[col_name].mean()
        except Exception as e:
            logger.info(
                f"Unable to read Intel Power Gadget logged file at {self._log_file_path}\n \
                Exception occurred %s",
                e,
                exc_info=True,
            )
        return cpu_details

    def start(self) -> None:
        """
        Placeholder method for starting the Intel Power Gadget monitoring.
        """
        # TODO: Read energy


class IntelRAPL:
    """
    A class to interface Intel's Running Average Power Limit (RAPL) for monitoring CPU power consumption.

    This class provides methods to set up and read energy consumption data from Intel RAPL files,
    which are available on Linux systems.
    It enables the measurement of CPU energy usage over time and provides methods to fetch
    both dynamic and static CPU energy details.

    Attributes:
        _lin_rapl_dir (str): The directory path where Intel RAPL files are located.
        _system (str): The platform of the running system, typically used to ensure compatibility.
        _rapl_files (List[RAPLFile]): A list of RAPLFile objects representing the files to read energy data from.
        _cpu_details (Dict): A dictionary storing the latest CPU energy details.
        _last_mesure (int): Placeholder for storing the last measurement time.

    Methods:
        start():
            Starts monitoring CPU energy consumption.

        get_cpu_details(duration: Time) -> Dict:
            Fetches the CPU energy deltas over a specified duration by reading values from RAPL files.

        get_static_cpu_details() -> Dict:
            Returns the CPU details without recalculating them.

    """

    def __init__(self, rapl_dir="/sys/class/powercap/intel-rapl/subsystem"):
        self._lin_rapl_dir = rapl_dir
        self._system = sys.platform.lower()
        self._rapl_files = []
        self._setup_rapl()
        self._cpu_details: Dict = {}

        self._last_mesure = 0

    def _is_platform_supported(self) -> bool:
        return self._system.startswith("lin")

    def _setup_rapl(self) -> None:
        if self._is_platform_supported():
            if os.path.exists(self._lin_rapl_dir):
                self._fetch_rapl_files()
            else:
                raise FileNotFoundError(
                    f"Intel RAPL files not found at {self._lin_rapl_dir} "
                    + f"on {self._system}"
                )
        else:
            raise SystemError("Platform not supported by Intel RAPL Interface")

    def _fetch_rapl_files(self) -> None:
        """
        Fetches RAPL files from the RAPL directory
        """

        # consider files like `intel-rapl:$i`
        files = list(filter(lambda x: ":" in x, os.listdir(self._lin_rapl_dir)))

        i = 0
        for file in files:
            path = os.path.join(self._lin_rapl_dir, file, "name")
            with open(path) as f:
                name = f.read().strip()
                # Fake the name used by Power Gadget
                # We ignore "core" in name as it seems to be included in "package" for Intel CPU.
                # TODO: Use "dram" for memory power
                if "package" in name:
                    name = f"Processor Energy Delta_{i}(kWh)"
                    i += 1
                # RAPL file to take measurement from
                rapl_file = os.path.join(self._lin_rapl_dir, file, "energy_uj")
                # RAPL file containing maximum possible value of energy_uj above which it wraps
                rapl_file_max = os.path.join(
                    self._lin_rapl_dir, file, "max_energy_range_uj"
                )
                try:
                    # Try to read the file to be sure we can
                    with open(rapl_file, "r") as f:
                        _ = float(f.read())
                    self._rapl_files.append(
                        RAPLFile(name=name, path=rapl_file, max_path=rapl_file_max)
                    )
                    logger.debug("We will read Intel RAPL files at %s", rapl_file)
                except PermissionError as e:
                    raise PermissionError(
                        "PermissionError : Unable to read Intel RAPL files for CPU power, we will use a constant for your CPU power."
                        + " Please view https://github.com/mlco2/codecarbon/issues/244"
                        + " for workarounds : %s",
                        e,
                    ) from e

    def get_cpu_details(self, duration: Time) -> Dict:
        """
        Fetches the CPU Energy Deltas by fetching values from RAPL files
        """
        cpu_details = {}
        try:
            list(map(lambda rapl_file: rapl_file.delta(duration), self._rapl_files))

            for rapl_file in self._rapl_files:
                logger.debug(rapl_file)
                cpu_details[rapl_file.name] = rapl_file.energy_delta.kWh
                # We fake the name used by Power Gadget when using RAPL
                if "Energy" in rapl_file.name:
                    cpu_details[rapl_file.name.replace("Energy", "Power")] = (
                        rapl_file.power.W
                    )
        except Exception as e:
            logger.info(
                "Unable to read Intel RAPL files at %s\n \
                Exception occurred %s",
                self._rapl_files,
                e,
                exc_info=True,
            )
        self._cpu_details = cpu_details
        logger.debug("get_cpu_details %s", self._cpu_details)
        return cpu_details

    def get_static_cpu_details(self) -> Dict:
        """
        Return CPU details without computing them.
        """
        return self._cpu_details

    def start(self) -> None:
        """
        Starts monitoring CPU energy consumption.
        """
        for rapl_file in self._rapl_files:
            rapl_file.start()


class TDP:
    """
    Represents Thermal Design Power (TDP) for detecting and estimating
    the power consumption of the CPU on a machine.

    The class provides methods to identify the CPU model, match it with known TDP
    values from a dataset, and return the corresponding power consumption in watts.

    Attributes:
        model (str): The detected CPU model name.
        tdp (int): The TDP value of the detected CPU in watts.

    Methods:
        start():
            Placeholder method to initiate TDP analysis.

    """

    def __init__(self):
        self.model, self.tdp = self._main()

    @staticmethod
    def _get_cpu_constant_power(match: str, cpu_power_df: pd.DataFrame) -> int:
        """Extract constant power from matched CPU"""
        return float(cpu_power_df[cpu_power_df["Name"] == match]["TDP"].values[0])

    def _get_cpu_power_from_registry(self, cpu_model_raw: str) -> Optional[int]:
        cpu_power_df = DataSource().get_cpu_power_data()
        cpu_matching = self._get_matching_cpu(cpu_model_raw, cpu_power_df)
        if cpu_matching:
            power = self._get_cpu_constant_power(cpu_matching, cpu_power_df)
            return power
        return None

    def _get_matching_cpu(
        self, model_raw: str, cpu_df: pd.DataFrame, greedy=False
    ) -> str:
        """
        Get matching cpu name

        :args:
            model_raw (str): raw name of the cpu model detected on the machine

            cpu_df (DataFrame): table containing cpu models along their tdp

            greedy (default False): if multiple cpu models match with an equal
            ratio of similarity, greedy (True) selects the first model,
            following the order of the cpu list provided, while non-greedy
            returns None.

        :return: name of the matching cpu model

        :notes:
            Thanks to the greedy mode, even though the match could be a model
            with a tdp very different from the actual tdp of current cpu, it
            still enables the relative comparison of models emissions running
            on the same machine.

            THRESHOLD_DIRECT defines the similarity ratio value to consider
            almost-exact matches.

            THRESHOLD_TOKEN_SET defines the similarity ratio value to consider
            token_set matches (for more detail see fuzz.token_set_ratio).
        """
        THRESHOLD_DIRECT: int = 100
        THRESHOLD_TOKEN_SET: int = 100

        direct_match = process.extractOne(
            model_raw,
            cpu_df["Name"],
            processor=lambda s: s.lower(),
            scorer=fuzz.ratio,
            score_cutoff=THRESHOLD_DIRECT,
        )

        if direct_match:
            return direct_match[0]

        model_raw = model_raw.replace("(R)", "")
        start_cpu = model_raw.find(" CPU @ ")
        if start_cpu > 0:
            model_raw = model_raw[0:start_cpu]
        model_raw = model_raw.replace(" CPU", "")
        model_raw = re.sub(r" @\s*\d+\.\d+GHz", "", model_raw)
        direct_match = process.extractOne(
            model_raw,
            cpu_df["Name"],
            processor=lambda s: s.lower(),
            scorer=fuzz.ratio,
            score_cutoff=THRESHOLD_DIRECT,
        )

        if direct_match:
            return direct_match[0]
        indirect_matches = process.extract(
            model_raw,
            cpu_df["Name"],
            processor=utils.default_process,
            scorer=fuzz.token_set_ratio,
            score_cutoff=THRESHOLD_TOKEN_SET,
        )

        if indirect_matches:
            if (
                greedy
                or len(indirect_matches) == 1
                or indirect_matches[0][1] != indirect_matches[1][1]
            ):
                return indirect_matches[0][0]

        return None

    def _main(self) -> Tuple[str, int]:
        """
        Get CPU power from constant mode

        :return: model name (str), power in Watt (int)
        """
        cpu_model_detected = detect_cpu_model()

        if cpu_model_detected:
            power = self._get_cpu_power_from_registry(cpu_model_detected)

            if power:
                logger.debug(
                    "CPU : We detect a %s with a TDP of %s W",
                    cpu_model_detected,
                    power,
                )
                return cpu_model_detected, power
            logger.warning(
                "We saw that you have a %s but we don't know it."
                + " Please contact us.",
                cpu_model_detected,
            )
            if is_psutil_available():
                # Count thread of the CPU
                threads = psutil.cpu_count(logical=True)
                estimated_tdp = threads * DEFAULT_POWER_PER_CORE
                logger.warning(
                    f"We will use the default power consumption of {DEFAULT_POWER_PER_CORE} W per thread for your {threads} CPU, so {estimated_tdp}W."
                )
                return cpu_model_detected, estimated_tdp
            return cpu_model_detected, None
        logger.warning(
            "We were unable to detect your CPU using the `cpuinfo` package."
            + " Resorting to a default power consumption."
        )
        return "Unknown", None

    def start(self):
        pass
