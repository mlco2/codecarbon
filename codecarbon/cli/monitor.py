"""
Implementations of the ``codecarbon monitor`` subcommand.
"""
import os
import subprocess as sp
import time
from typing import Sequence

from codecarbon import EmissionsTracker


def monitor_infinite_loop(measure_power_secs, api_call_interval, api):
    """
    Monitor all activity on the system until a user presses CTRL-C.
    """
    with EmissionsTracker(
        measure_power_secs=measure_power_secs,
        api_call_interval=api_call_interval,
        save_to_api=api,
        tracking_mode="machine",
    ):
        while True:
            time.sleep(300)


def monitor_subprocess(
    measure_power_secs, api_call_interval, api, cmd: Sequence[str | os.PathLike]
) -> int:
    """
    Run and monitor a subprocess.

    :return: return code of the subprocess.
    """

    with EmissionsTracker(
        measure_power_secs=measure_power_secs,
        api_call_interval=api_call_interval,
        save_to_api=api,
        tracking_mode="process",
    ):
        proc = sp.run(cmd)
    return proc.returncode
