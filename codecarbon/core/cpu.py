"""
Implements tracking Intel CPU Power Consumption on Mac and Windows
using Intel Power Gadget
https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html
"""

import os
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz, process, utils

from codecarbon.core.rapl import RAPLFile
from codecarbon.core.units import Time
from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger
from codecarbon.input import DataSource


def is_powergadget_available() -> bool:
    try:
        IntelPowerGadget()
        return True
    except Exception as e:
        logger.debug(
            "Not using PowerGadget, an exception occurred while instantiating"
            + f" IntelPowerGadget : {e}",
        )
        return False


def is_rapl_available() -> bool:
    try:
        IntelRAPL()
        return True
    except Exception as e:
        logger.debug(
            "Not using the RAPL interface, an exception occurred while instantiating "
            + f"IntelRAPL : {e}",
        )
        return False


class IntelPowerGadget:
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
                + f"Intel Power Gadget: {returncode}"
            )

    def get_cpu_details(self, **kwargs) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from a logged csv file
        in _log_values function
        """
        self._log_values()
        cpu_details = dict()
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
                Exception occurred {e}",
                exc_info=True,
            )
        return cpu_details

    def start(self):
        # TODO: Read energy
        pass


class IntelRAPL:
    def __init__(self, rapl_dir="/sys/class/powercap/intel-rapl"):
        self._lin_rapl_dir = rapl_dir
        self._system = sys.platform.lower()
        self._rapl_files = list()
        self._setup_rapl()
        self._cpu_details: Dict = dict()

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

    def _fetch_rapl_files(self):
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
                    logger.debug(f"We will read Intel RAPL files at {rapl_file}")
                except PermissionError as e:
                    raise PermissionError(
                        "Unable to read Intel RAPL files for CPU power, we will use a constant for your CPU power."
                        + " Please view https://github.com/mlco2/codecarbon/issues/244"
                        + f" for workarounds : {e}"
                    )

    def get_cpu_details(self, duration: Time, **kwargs) -> Dict:
        """
        Fetches the CPU Energy Deltas by fetching values from RAPL files
        """
        cpu_details = dict()
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
                f"Unable to read Intel RAPL files at {self._rapl_files}\n \
                Exception occurred {e}",
                exc_info=True,
            )
        self.cpu_details = cpu_details
        logger.debug(f"get_cpu_details {self.cpu_details}")
        return cpu_details

    def get_static_cpu_details(self) -> Dict:
        """
        Return CPU details without computing them.
        """
        logger.debug(f"get_static_cpu_details {self.cpu_details}")

        return self.cpu_details

    def start(self):
        for rapl_file in self._rapl_files:
            rapl_file.start()


class TDP:
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
        THRESHOLD_DIRECT = 100
        THRESHOLD_TOKEN_SET = 100

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
                    f"CPU : We detect a {cpu_model_detected} with a TDP of {power} W"
                )
                return cpu_model_detected, power
            logger.warning(
                f"We saw that you have a {cpu_model_detected} but we don't know it."
                + " Please contact us."
            )
            return cpu_model_detected, None
        logger.warning(
            "We were unable to detect your CPU using the `cpuinfo` package."
            + " Resorting to a default power consumption of 85W."
        )
        return "Unknown", None

    def start(self):
        pass
