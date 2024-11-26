import multiprocessing

from codecarbon import EmissionsTracker

# pool = SafePool(multiprocessing.cpu_count(), retries=150)
# handles = {
#     pool.submit(_preprocess, page): #LAMBDA FONCTION A APPLIQUER
# }
# results = []
# failures = []
# for result in pool.results():
#     i = handles[result.handle]
#     results.append((i, result.value))
#     if not result.ok():
#         failures.append(result.value)

# if failures:
#     raise failures.pop()


def task(number):
    a = 0
    for i in range(1000):
        for i in range(int(1e6)):
            a = a + i**number


tracker = EmissionsTracker(measure_power_secs=10, force_add_mode_cpu_load=True)
try:
    tracker.start()
    with multiprocessing.Pool() as pool:
        # call the function for each item in parallel
        pool.map(task, [i for i in range(100)])
finally:
    emissions: float = tracker.stop()

print(f"Emissions: {emissions} kg")
