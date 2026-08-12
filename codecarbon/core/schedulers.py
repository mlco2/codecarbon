"""
Detection of HPC batch scheduler job metadata.

Schedulers export the identity of the running job into the environment of every
job step, so no scheduler library is needed: reading ``os.environ`` is enough.

SLURM is detected automatically. Any other scheduler is supported through the
generic ``CODECARBON_JOB_*`` environment contract, which also takes precedence
over the auto-detected values, so a site can map its own scheduler in a couple
of lines of shell.
"""

import os
import re
from typing import Dict

from codecarbon.external.logger import logger

# Field name on EmissionsData -> SLURM environment variable holding it.
SLURM_ENV_VARS = {
    "job_id": "SLURM_JOB_ID",
    "job_name": "SLURM_JOB_NAME",
    "job_user": "SLURM_JOB_USER",
    "job_account": "SLURM_JOB_ACCOUNT",
    "job_partition": "SLURM_JOB_PARTITION",
    "node_name": "SLURMD_NODENAME",
}

JOB_METADATA_FIELDS = ("scheduler",) + tuple(SLURM_ENV_VARS)


def detect_job_metadata() -> Dict[str, str]:
    """
    Collect the scheduler job metadata of the current process.

    :return: a dict with one entry per field of ``JOB_METADATA_FIELDS``, with
        empty strings for everything that could not be detected. Outside of a
        batch job every value is empty.
    """
    metadata = {field: "" for field in JOB_METADATA_FIELDS}

    if os.environ.get("SLURM_JOB_ID"):
        metadata["scheduler"] = "slurm"
        for field, env_var in SLURM_ENV_VARS.items():
            metadata[field] = os.environ.get(env_var, "")

    # Explicit configuration always wins, whatever the scheduler.
    for field in JOB_METADATA_FIELDS:
        override = os.environ.get(f"CODECARBON_{field.upper()}")
        if override:
            metadata[field] = override

    return metadata


def warn_on_multi_rank_double_counting(tracking_mode: str) -> None:
    """
    Warn when several ranks share a node and each one measures the whole node.

    In ``machine`` mode every rank reports the node's power, so the job's
    reported footprint is silently multiplied by the number of ranks per node.
    """
    if tracking_mode != "machine":
        return
    # SLURM writes this as "4", or as "4(x2)" for a heterogeneous allocation.
    match = re.match(r"\d+", os.environ.get("SLURM_NTASKS_PER_NODE", ""))
    if match and int(match.group()) > 1:
        logger.warning(
            f"SLURM_NTASKS_PER_NODE is {os.environ['SLURM_NTASKS_PER_NODE']} and "
            "tracking_mode is 'machine': every rank measures the whole node, so "
            "the job's total will be multiplied by the number of ranks per node. "
            "Start the tracker on one rank per node (SLURM_LOCALID == 0), or use "
            "tracking_mode='process'."
        )
