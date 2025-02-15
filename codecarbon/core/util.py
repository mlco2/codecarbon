import os
import re
import subprocess
import sys
from contextlib import contextmanager
from os.path import expandvars
from pathlib import Path
from typing import Optional, Union

import cpuinfo
import psutil

from codecarbon.external.logger import logger

SLURM_JOB_ID = os.environ.get(
    "SLURM_JOB_ID",  # default
    os.environ.get("SLURM_JOBID"),  # deprecated but may still be used
)


@contextmanager
def suppress(*exceptions):
    try:
        yield
    except exceptions:
        logger.warning("graceful shutdown. Exceptions:")
        logger.warning(
            exceptions if len(exceptions) != 1 else exceptions[0], exc_info=True
        )
        logger.warning("stopping.")


def resolve_path(path: Union[str, Path]) -> Path:
    """
    Fully resolve a path:
    resolve env vars ($HOME etc.) -> expand user (~) -> make absolute

    Args:
        path (Union[str, Path]): Path to a file or repository to resolve as
            string or pathlib.Path

    Returns:
        pathlib.Path: resolved absolute path
    """
    return Path(expandvars(str(path))).expanduser().resolve()


def backup(file_path: Union[str, Path], ext: Optional[str] = ".bak") -> None:
    """
    Resolves the path to a path then backs it up, adding the extension provided.
    Warning : this function will rename the file in place, it's the calling function that will write a new file at the original path.
    This function will not overwrite existing backups but add a number.

    Args:
        file_path (Union[str, Path]): Path to a file to backup.
        ext (Optional[str], optional): extension to append to the filename when
            backing it up. Defaults to ".bak".
    """
    file_path = resolve_path(file_path)
    if not file_path.exists():
        return
    assert file_path.is_file()
    idx = 0
    parent = file_path.parent
    file_name = f"{file_path.name}{ext}"
    backup_path = parent / file_name

    while backup_path.exists():
        file_name = f"{file_path.name}_{idx}{ext}"
        backup_path = parent / file_name
        idx += 1

    file_path.rename(backup_path)


def detect_cpu_model() -> str:
    cpu_info = cpuinfo.get_cpu_info()
    if cpu_info:
        cpu_model_detected = cpu_info.get("brand_raw", "")
        return cpu_model_detected
    return None


def is_mac_os() -> str:
    system = sys.platform.lower()
    return system.startswith("dar")


def is_windows_os() -> str:
    system = sys.platform.lower()
    return system.startswith("win")


def is_linux_os() -> str:
    system = sys.platform.lower()
    return system.startswith("lin")


def count_physical_cpus():
    import platform
    import subprocess

    if platform.system() == "Windows":
        return int(os.environ.get("NUMBER_OF_PROCESSORS", 1))
    else:
        try:
            output = subprocess.check_output(["lscpu"], text=True)
            for line in output.split("\n"):
                if "Socket(s):" in line:
                    return int(line.split(":")[1].strip())
            else:
                return 1
        except Exception as e:
            logger.warning(
                f"Error while trying to count physical CPUs: {e}. Defaulting to 1."
            )
            return 1


def count_cpus() -> int:
    if SLURM_JOB_ID is None:
        return psutil.cpu_count()

    try:
        logger.debug(
            "SLURM environment detected for job {SLURM_JOB_ID}, running"
            + " `scontrol show job $SLURM_JOB_ID` to count SLURM-available cpus."
        )
        scontrol = subprocess.check_output(
            [f"scontrol show job {SLURM_JOB_ID}"], shell=True
        ).decode()
    except subprocess.CalledProcessError:
        logger.warning(
            "Error running `scontrol show job $SLURM_JOB_ID` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count(logical=True)

    num_cpus_matches = re.findall(r"NumCPUs=\d+", scontrol)

    if len(num_cpus_matches) == 0:
        logger.warning(
            "Could not find NumCPUs= after running `scontrol show job $SLURM_JOB_ID` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count(logical=True)

    if len(num_cpus_matches) > 1:
        logger.warning(
            "Unexpected output after running `scontrol show job $SLURM_JOB_ID` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count(logical=True)

    num_cpus = num_cpus_matches[0].replace("NumCPUs=", "")
    logger.debug(f"Detected {num_cpus} cpus available on SLURM.")
    return int(num_cpus)
