import multiprocessing
from time import sleep

from codecarbon import EmissionsTracker


def no_load_task(number):
    sleep(60)


def cpu_load_task(number):
    a = 0
    for i in range(1000):
        for i in range(int(1e6)):
            a = a + i**number


tracker = EmissionsTracker(
    measure_power_secs=10, force_mode_cpu_load=False, log_level="debug"
)
try:
    tracker.start()
    with multiprocessing.Pool() as pool:
        # call the function for each item in parallel
        pool.map(cpu_load_task, [i for i in range(100)])
finally:
    emissions: float = tracker.stop()

print(f"Emissions: {emissions} kg")
