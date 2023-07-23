"""
Implementations of the ``codecarbon monitor`` subcommand.
"""
import time

from codecarbon import EmissionsTracker


def monitor_infinite_loop(measure_power_secs, api_call_interval, api):
    """
    Monitor all activity on the system until a user presses CTRL-C.
    """
    with EmissionsTracker(
        measure_power_secs=measure_power_secs,
        api_call_interval=api_call_interval,
        save_to_api=api,
    ):
        while True:
            time.sleep(300)
