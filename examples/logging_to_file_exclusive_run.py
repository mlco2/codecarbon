"""
Similar to logging_to_file.py, but with the `prevent_multiple_runs` parameter set to True.
This will prevent multiple instances of codecarbon from running at the same time.
We run 5 instances of codecarbon. 4 wil fail and only one will succeed

"""

import multiprocessing
import time

from codecarbon import OfflineEmissionsTracker


def train_model():
    """
    This function will do nothing during (occurrence * delay) seconds.
    The Code Carbon API will be called every (measure_power_secs * api_call_interval) seconds.
    """
    occurrence = 60 * 24 * 365 * 100  # Run for 100 years!
    delay = 60  # Seconds
    for i in range(occurrence):
        print(f"{occurrence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


def worker():
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=30,
        project_name="ultra_secret",
        prevent_multiple_runs=True,
    )

    tracker.start()
    try:
        train_model()
    finally:
        tracker.stop()


if __name__ == "__main__":
    for _ in range(5):
        p = multiprocessing.Process(target=worker)
        p.start()
