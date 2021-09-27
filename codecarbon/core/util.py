import logging
import os
import re
import subprocess

from contextlib import contextmanager
from os.path import expandvars
from pathlib import Path
from typing import Optional, Union

import cpuinfo
import psutil

from codecarbon.external.logger import logger


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
        pass


def resolve_path(path: Union[str, Path]) -> None:

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
    backup = parent / file_name

    while backup.exists():
        file_name = f"{file_path.name}_{idx}{ext}"
        backup = parent / file_name
        idx += 1

    file_path.rename(backup)


def detect_cpu_model() -> str:
    cpu_info = cpuinfo.get_cpu_info()
    if cpu_info:
        cpu_model_detected = cpu_info.get("brand_raw", "")
        return cpu_model_detected
    else:
        return None


def count_cpus() -> int:
    if os.environ.get("SLURM_JOB_ID") is None:
        return psutil.cpu_count()

    try:
        scontrol = subprocess.check_output(
            ["scontrol show job $SLURM_JOBID"], shell=True
        ).decode()
    except subprocess.CalledProcessError:
        logger.warning(
            "Error running `scontrol show job $SLURM_JOBID` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count()

    num_cpus_matches = re.findall(r"NumCPUs=\d+", scontrol)

    if len(num_cpus_matches) == 0:
        logger.warning(
            "Could not find NumCPUs= after running `scontrol show job $SLURM_JOBID` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count()

    if len(num_cpus_matches) > 1:
        logger.warning(
            "Unexpected output after running `scontrol show job $SLURM_JOBID` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count()

    num_cpus = num_cpus_matches[0].replace("NumCPUs=", "")
    return int(num_cpus)
