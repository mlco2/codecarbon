import os

from codecarbon.external.logger import logger


def warn_on_multi_rank_double_counting(tracking_mode: str) -> None:
    """
    Warn when a machine-mode tracker runs on a non-zero SLURM local rank.

    In ``machine`` mode every tracker reports the whole node's power, so if
    more than one rank per node starts a tracker, the job's footprint is
    silently multiplied. Local rank 0 (the recommended tracker) and the batch
    step (``SLURM_LOCALID`` unset) never warn.
    """
    if tracking_mode != "machine":
        return
    local_id = os.environ.get("SLURM_LOCALID", "")
    if not local_id.isdigit() or int(local_id) == 0:
        return
    # Step-scoped and always set by srun; written "4", or "4(x2)".
    tasks_per_node = os.environ.get(
        "SLURM_STEP_TASKS_PER_NODE", os.environ.get("SLURM_TASKS_PER_NODE", "?")
    )
    logger.warning(
        f"tracking_mode is 'machine' on SLURM local rank {local_id} "
        f"(tasks per node: {tasks_per_node}). If more than one rank per node "
        "starts a tracker, each one measures the whole node and the job's total "
        "is multiplied. Start the tracker only on SLURM_LOCALID == 0, or use "
        "tracking_mode='process'."
    )
