import random
import threading
import time

from codecarbon import OfflineEmissionsTracker


def tracker_example():
    """
    This function will do nothing during (occurrence * delay) seconds.
    """
    occurrence = random.randint(1, 3)  # Run for 1 to 3 seconds
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=30,
        project_name="ultra_secret",
    )

    tracker.start()
    try:
        delay = 1  # Seconds
        for _ in range(occurrence):
            time.sleep(delay)
    finally:
        tracker.stop()


if __name__ == "__main__":

    threads = []
    for _ in range(3):
        t = threading.Thread(target=tracker_example)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
