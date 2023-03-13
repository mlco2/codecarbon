from codecarbon import EmissionsTracker

a = 0
tracker = EmissionsTracker(measure_power_secs=100)
try:
    tracker.start()
    for i in range(100):
        for i in range(int(1e6)):
            a = a + i**5
finally:
    emissions: float = tracker.stop()

print(a)
print(f"Emissions: {emissions} kg")
