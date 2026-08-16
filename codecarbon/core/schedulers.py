"""
Detection of the HPC batch scheduler job identity.

Schedulers export the identity of the running job into the environment of every
job step, so no scheduler library is needed: reading ``os.environ`` is enough.

SLURM is detected automatically. Any other scheduler is supported through the
generic ``CODECARBON_SCHEDULER_JOB_ID`` environment variable, which also takes
precedence over the auto-detected value, so a site can map its own scheduler in
one line of shell.
"""

import os


def detect_scheduler_job_id() -> str:
    """
    Return the batch scheduler job ID of the current process, or "" outside of
    a batch job.

    Only the job ID is collected: it is the join key, and everything else the
    scheduler knows about the job (name, account, partition, node) is one
    ``sacct -j <id>`` away.
    """
    return os.environ.get("CODECARBON_SCHEDULER_JOB_ID") or os.environ.get(
        "SLURM_JOB_ID", ""
    )
