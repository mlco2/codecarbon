import multiprocessing

from codecarbon import EmissionsTracker, OutputMethod


def cpu_load_task(number):
    a = 0
    for i in range(5):
        for i in range(int(1e6)):
            a = a + i**number


tracker = EmissionsTracker(
    measure_power_secs=10,
    force_mode_cpu_load=False,
    log_level="debug",
    output_methods=[OutputMethod.BOAMPS],
)
try:
    tracker.start()
    with multiprocessing.Pool() as pool:
        # call the function for each item in parallel
        pool.map(cpu_load_task, [i for i in range(100)])
finally:
    emissions = tracker.stop()

print(f"Emissions: {emissions} kg")
print(f"BoAmps report written to ./boamps_report_{tracker.run_id}.json")
