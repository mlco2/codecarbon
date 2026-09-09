import os
import re

from codecarbon.external.logger import logger


def warn_on_multi_rank_double_counting(tracking_mode: str) -> None:
    """
    Warn when several ranks share a node and each one measures the whole node.

    In ``machine`` mode every rank reports the node's power, so the job's
    reported footprint is silently multiplied by the number of ranks per node.
    """
    if tracking_mode != "machine":
        return
    # SLURM writes this as "4", or as "4(x2)" for a heterogeneous allocation.
    ntasks_per_node = os.environ.get("SLURM_NTASKS_PER_NODE", "")
    match = re.match(r"\d+", ntasks_per_node)
    if match and int(match.group()) > 1:
        logger.warning(
            f"SLURM_NTASKS_PER_NODE is {ntasks_per_node} and tracking_mode is "
            "'machine': every rank measures the whole node, so the job's total "
            "will be multiplied by the number of ranks per node. Start the "
            "tracker on one rank per node (SLURM_LOCALID == 0), or use "
            "tracking_mode='process'."
        )
