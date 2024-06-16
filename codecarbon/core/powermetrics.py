import os
import re
import shutil
import subprocess
import sys
from typing import Dict

import numpy as np

from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger


def is_powermetrics_available():
    try:
        ApplePowermetrics()
        response = _has_powermetrics_sudo()
        return response
    except Exception as e:
        logger.debug(
            "Not using PowerMetrics, an exception occurred while instantiating"
            + f" Powermetrics : {e}",
        )
        return False


def _has_powermetrics_sudo():
    if shutil.which("sudo") is None:
        logger.debug("sudo not available, we won't use Apple PowerMetrics.")
        return False
    if shutil.which("powermetrics") is None:
        logger.info(
            "Apple PowerMetrics not available. Please install it if you are using an Apple product."
        )
        return False
    process = subprocess.Popen(
        [
            "sudo",
            "powermetrics",
            "--samplers",
            "cpu_power",
            "-n",
            "1",
            "-i",
            "1",
            "-o",
            "/dev/null",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    _, stderr = process.communicate()

    if re.search(r"[sudo].*password", stderr):
        logger.debug(
            """Not using PowerMetrics, sudo password prompt detected.
                If you want to enable Powermetrics please modify your sudoers file
                as described in :
                https://mlco2.github.io/codecarbon/methodology.html#power-usage
            """
        )
        return False
    if process.returncode != 0:
        raise Exception("Return code != 0")
    else:
        return True


class ApplePowermetrics:
    _osx_silicon_exec = "powermetrics"

    def __init__(
        self,
        output_dir: str = ".",
        n_points=10,
        interval=100,
        log_file_name="powermetrics_log.txt",
    ):
        self._log_file_path = os.path.join(output_dir, log_file_name)
        self._system = sys.platform.lower()
        self._n_points = n_points
        self._interval = interval
        self._setup_cli()

    def _setup_cli(self):
        """
        Setup cli command to run Powermetrics
        """
        if self._system.startswith("darwin"):
            cpu_model = detect_cpu_model()
            if cpu_model.startswith("Apple"):
                if shutil.which(self._osx_silicon_exec):
                    self._cli = self._osx_silicon_exec
                else:
                    raise FileNotFoundError(
                        f"Powermetrics executable not found on {self._system}"
                    )
        else:
            raise SystemError("Platform not supported by Powermetrics")

    def _log_values(self):
        """
        Logs output from Powermetrics to a file
        """
        returncode = None

        if self._system.startswith("darwin"):
            # Run the powermetrics command with sudo and capture its output
            cmd = [
                "sudo",
                "powermetrics",
                "-n",
                str(self._n_points),
                "",
                "--samplers",
                "cpu_power",
                "--format",
                "csv",
                "-i",
                str(self._interval),
                "-o",
                self._log_file_path,
            ]
            returncode = subprocess.call(cmd, universal_newlines=True)

        else:
            return None

        if returncode != 0:
            logger.warning(
                "Returncode while logging power values using "
                + f"Powermetrics: {returncode}"
            )
        return

    def get_details(self, **kwargs) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from a logged csv file
        in _log_values function
        """
        self._log_values()
        details = dict()
        try:
            with open(self._log_file_path) as f:
                logfile = f.read()
            cpu_pattern = r"CPU Power: (\d+) mW"
            cpu_power_list = re.findall(cpu_pattern, logfile)

            details["CPU Power"] = np.mean(
                [float(power) / 1000 for power in cpu_power_list]
            )
            details["CPU Energy Delta"] = np.sum(
                [
                    (self._interval / 1000) * (float(power) / 1000)
                    for power in cpu_power_list
                ]
            )
            gpu_pattern = r"GPU Power: (\d+) mW"
            gpu_power_list = re.findall(gpu_pattern, logfile)
            details["GPU Power"] = np.mean(
                [float(power) / 1000 for power in gpu_power_list]
            )
            details["GPU Energy Delta"] = np.sum(
                [
                    (self._interval / 1000) * (float(power) / 1000)
                    for power in gpu_power_list
                ]
            )
        except Exception as e:
            logger.info(
                f"Unable to read Powermetrics logged file at {self._log_file_path}\n \
                Exception occurred {e}",
                exc_info=True,
            )
        return details

    def start(self):
        # TODO: Read energy
        pass
