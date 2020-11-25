"""
Implements tracking Intel CPU Power Consumption on Mac and Windows
using Intel Power Gadget https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html
"""
import os
import shutil
import subprocess
import sys
import time
from logging import getLogger
from typing import Dict

import pandas as pd

from codecarbon.core.rapl import RAPLFile

logger = getLogger(__name__)


def is_powergadget_available():
    try:
        IntelPowerGadget()
        return True
    except Exception as e:
        logger.debug(
            f"Exception occurred while instantiating IntelPowerGadget : {e}",
            exc_info=True,
        )
        return False


def is_rapl_available():
    import traceback
    try:
        IntelRAPLInterface()
        return True
    except Exception as e:
        logger.debug(
            f"Exception occurred while instantiating RAPLInterface : {e}", exc_info=True
        )
        return False


class IntelPowerGadget:
    _osx_exec = "PowerLog"
    _osx_exec_backup = "/Applications/Intel Power Gadget/PowerLog"
    _windows_exec = "PowerLog3.0.exe"
    _windows_exec_backup = "C:\\Program Files\\Intel\\Power Gadget 3.5\\"

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

    def _setup_cli(self):
        """
        Setup cli command to run Intel Power Gadget
        """
        if self._system.startswith("win"):
            if shutil.which(self._windows_exec):
                self._cli = self._windows_exec
            elif shutil.which(self._windows_exec, path=self._windows_exec_backup):
                self._cli = shutil.which(
                    self._windows_exec, path=self._windows_exec_backup
                )
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

    def _log_values(self):
        """
        Logs output from Intel Power Gadget command line to a file
        """
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
        logger.debug("PowerLog returncode %d", returncode)
        return

    def get_cpu_details(self) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from a logged csv file in _log_values function
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
            logger.debug(
                f"CODECARBON Unable to read Intel Power Gadget logged file at {self._log_file_path}\n \
                Exception occurred {e}",
                exc_info=True,
            )

        return cpu_details


class IntelRAPLInterface:
    _lin_rapl_dir = "/sys/class/powercap/intel-rapl"

    def __init__(self, output_dir: str = ".", log_file_name="intel_rapl_log.csv"):
        self._log_file_path = os.path.join(output_dir, log_file_name)
        self._system = sys.platform.lower()
        self._delay = 0.01  # 10 millisecond
        self._rapl_files = list()
        self._setup_rapl()

    def _setup_rapl(self):
        if self._system.startswith("lin"):
            if os.path.exists(self._lin_rapl_dir):
                self._fetch_rapl_files()
            else:
                raise FileNotFoundError(
                    f"Intel RAPL files not found at {self._lin_rapl_dir} on {self._system}"
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
                name = f.read()[:-1]
                if "package" in name:
                    renamed = f"Processor Power_{i}(Watt)"
                    i += 1
                self._rapl_files.append(
                    RAPLFile(
                        renamed, os.path.join(self._lin_rapl_dir, file, "energy_uj")
                    )
                )

    def get_cpu_details(self) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from RAPL files
        """
        cpu_details = dict()
        try:
            list(map(lambda rapl_file: rapl_file.start(), self._rapl_files))
            time.sleep(self._delay)
            list(map(lambda rapl_file: rapl_file.end(self._delay), self._rapl_files))
            for rapl_file in self._rapl_files:
                cpu_details[rapl_file.name] = rapl_file.power_measurement

        except Exception as e:
            logger.debug(
                f"CODECARBON Unable to read Intel RAPL files at {self._rapl_files}\n \
                Exception occurred {e}",
                exc_info=True,
            )
        return cpu_details
