"""
Read Apple Silicon power without sudo, using macmon.

macmon (https://github.com/vladkens/macmon) reads the same private IOReport
counters as ``powermetrics`` but runs as a normal user, so it needs neither
root nor a sudoers entry. Install it with ``brew install macmon``.
"""

import json
import shutil
import statistics
import subprocess
import sys
from functools import lru_cache
from typing import Dict, List

from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger

MACMON_EXECUTABLE = "macmon"

# macmon JSON field -> chip part name used by AppleSiliconChip
_CHIP_PART_FIELDS = {
    "CPU": "cpu_power",
    "GPU": "gpu_power",
}


@lru_cache(maxsize=1)
def is_macmon_available() -> bool:
    """
    True when we are on Apple Silicon and the macmon executable is on PATH.

    This only looks the executable up and does not run it, so it is cheap
    enough to try before the cpu_load fallback without slowing down startup.
    """
    try:
        MacMon()
        return True
    except Exception as e:
        logger.debug(f"Not using macmon: {e}")
        return False


def clear_macmon_cache() -> None:
    is_macmon_available.cache_clear()


def _kill_process(process: subprocess.Popen) -> None:
    """Kill a macmon subprocess, tolerating a failure to do so."""
    try:
        process.kill()
        process.wait(timeout=1)
    except (OSError, subprocess.SubprocessError):
        logger.debug("Could not kill the macmon process.")
    finally:
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()


class MacMon:
    """
    Read Apple Silicon CPU and GPU power with the ``macmon`` command-line tool.

    Each call to ``get_details`` runs ``macmon pipe`` for ``n_points`` samples
    of ``interval`` milliseconds and averages them. It exposes the same keys as
    ``ApplePowermetrics.get_details`` so that ``AppleSiliconChip`` can use
    either backend.
    """

    def __init__(self, n_points: int = 10, interval: int = 100) -> None:
        self._system = sys.platform.lower()
        self._n_points = n_points
        self._interval = interval
        self._setup_cli()

    def _setup_cli(self) -> None:
        if not self._system.startswith("darwin"):
            raise SystemError("Platform not supported by macmon")
        cpu_model = detect_cpu_model() or ""
        if not cpu_model.startswith("Apple"):
            raise SystemError(
                f"macmon is only supported on Apple Silicon, detected CPU: {cpu_model!r}"
            )
        cli = shutil.which(MACMON_EXECUTABLE)
        if cli is None:
            raise FileNotFoundError(
                "macmon executable not found, install it with `brew install macmon`"
                " or see https://github.com/vladkens/macmon"
            )
        self._cli = cli

    def _read_samples(self) -> List[Dict]:
        """
        Run macmon and return the parsed JSON samples.

        :return: an empty list when macmon failed, so the caller skips this
                 measure instead of reporting 0 W.
        """
        cmd = [
            self._cli,
            "pipe",
            "-s",
            str(self._n_points),
            "-i",
            str(self._interval),
        ]
        # Same heuristic as for powermetrics: twice the nominal runtime plus a
        # floor. It only has to bound a hang, never trip on a healthy run.
        timeout = self._n_points * self._interval / 1000 * 2 + 5
        # No context manager: Popen.__exit__ would wait() without a timeout.
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(
                f"macmon did not complete within {timeout:g} seconds, "
                "skipping this measure."
            )
            _kill_process(process)
            return []

        if process.returncode != 0:
            logger.warning(
                f"Returncode while logging power values using macmon: "
                f"{process.returncode} {stderr.strip()}"
            )
            return []

        samples = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                logger.debug(f"Ignoring a macmon line that is not JSON: {line!r}")
        return samples

    def get_details(self) -> Dict:
        """
        Average CPU and GPU power over one macmon run.

        :return: {"CPU Power": W, "CPU Energy Delta": J, "GPU Power": W, ...},
                 or an empty dict when macmon gave no sample.
        """
        samples = self._read_samples()
        if not samples:
            return dict()
        details = dict()
        for chip_part, field in _CHIP_PART_FIELDS.items():
            watts = [
                float(sample[field])
                for sample in samples
                if sample.get(field) is not None
            ]
            power = statistics.fmean(watts) if watts else 0.0
            details[f"{chip_part} Power"] = power
            details[f"{chip_part} Energy Delta"] = (
                power * len(watts) * self._interval / 1000
            )
        return details

    def start(self) -> None:
        pass
