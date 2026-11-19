import math
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from functools import lru_cache
from os.path import expandvars
from pathlib import Path
from typing import Optional, Union

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


@lru_cache(maxsize=1)
def detect_cpu_model() -> Optional[str]:
    import cpuinfo

    cpu_info = cpuinfo.get_cpu_info()
    if cpu_info:
        cpu_model_detected = cpu_info.get("brand_raw", "")
        return cpu_model_detected
    return None


def is_mac_os() -> bool:
    system = sys.platform.lower()
    return system.startswith("dar")


def is_mac_arm(cpu_model: str) -> bool:
    return bool(re.search(r"\bM\d{1,2}\b", cpu_model))


def is_windows_os() -> bool:
    system = sys.platform.lower()
    return system.startswith("win")


def is_linux_os() -> bool:
    system = sys.platform.lower()
    return system.startswith("lin")


def count_physical_cpus():
    import platform
    import subprocess

    if platform.system() == "Windows":
        return _windows_get_physical_sockets()
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


def _windows_get_physical_sockets():
    try:
        # use PowerShell to count number of objects of class Win32_Processor
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance -ClassName Win32_Processor).Count",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=True
        )

        output = result.stdout.strip() or "1"
        logger.debug(f"Detected {output} physical sockets on Windows.")
        return int(output)

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
        logger.error(f"Error detecting physical sockets on Windows: {e}")
        return 1  # Fallback:at least one socket


def _read_cgroup_cpu_limit(cgroup_dir, v2):
    try:
        if v2:
            with open(os.path.join(cgroup_dir, "cpu.max")) as f:
                quota, period = f.read().split()[:2]

            if quota == "max":
                return None
        else:
            with open(os.path.join(cgroup_dir, "cpu.cfs_quota_us")) as f:
                quota = f.read().strip()

            with open(os.path.join(cgroup_dir, "cpu.cfs_period_us")) as f:
                period = f.read().strip()

        quota = int(quota)
        period = int(period)

        if quota <= 0 or period <= 0:
            return None

        return quota / period

    except (OSError, ValueError):
        return None


def _cgroup_cpu_limit(proc_cgroup="/proc/self/cgroup", cgroup_root="/sys/fs/cgroup"):
    try:
        with open(proc_cgroup) as f:
            lines = f.read().splitlines()
    except OSError:
        return None

    limits = []

    for line in lines:
        parts = line.split(":", 2)

        if len(parts) != 3:
            continue

        controllers, path = parts[1], parts[2]

        if not controllers:
            mounts = [cgroup_root]
            v2 = True
        elif "cpu" in controllers.split(","):
            mounts = [
                os.path.join(cgroup_root, name)
                for name in ("cpu", "cpu,cpuacct", "cpuacct,cpu")
            ]
            v2 = False
        else:
            continue

        for mount in mounts:
            relative_path = path.strip("/")

            while True:
                limit = _read_cgroup_cpu_limit(os.path.join(mount, relative_path), v2)

                if limit is not None:
                    limits.append(limit)

                if not relative_path:
                    break

                relative_path = os.path.dirname(relative_path)

    return min(limits) if limits else None


def count_cpus() -> int:
    if SLURM_JOB_ID is None:
        cpu_count = None

        if hasattr(os, "sched_getaffinity"):
            try:
                cpu_count = len(os.sched_getaffinity(0))
            except OSError:
                pass

        if not cpu_count:
            cpu_count = psutil.cpu_count()

        cpu_quota = _cgroup_cpu_limit()

        if cpu_quota is not None and cpu_count:
            cpu_count = max(1, min(cpu_count, math.ceil(cpu_quota)))

        return cpu_count

    try:
        logger.debug(
            f"SLURM environment detected for job {SLURM_JOB_ID}, running"
            + f" `scontrol show job {SLURM_JOB_ID}` to count SLURM-available cpus."
        )
        scontrol = subprocess.check_output(
            ["scontrol", "show", "job", SLURM_JOB_ID]
        ).decode()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            f"Error running `scontrol show job {SLURM_JOB_ID}` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count(logical=True)

    num_cpus_matches = re.findall(r"NumCPUs=\d+", scontrol)

    if len(num_cpus_matches) == 0:
        logger.warning(
            f"Could not find NumCPUs= after running `scontrol show job {SLURM_JOB_ID}` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count(logical=True)

    if len(num_cpus_matches) > 1:
        logger.warning(
            f"Unexpected output after running `scontrol show job {SLURM_JOB_ID}` "
            + "to count SLURM-available cpus. Using the machine's cpu count."
        )
        return psutil.cpu_count(logical=True)

    num_cpus = num_cpus_matches[0].replace("NumCPUs=", "")
    logger.debug(f"Detected {num_cpus} cpus available on SLURM.")

    num_gpus_matches = re.findall(r"gres/gpu=\d+", scontrol)
    if len(num_gpus_matches) > 0:
        num_gpus = num_gpus_matches[0].replace("gres/gpu=", "")
        logger.debug(f"Detected {num_gpus} gpus available on SLURM.")

    return int(num_cpus)
