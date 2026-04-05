# test_temp.py
import time
import pandas as pd
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    project_name="temperature_test",
    measure_power_secs=15,
    save_to_file=True,
    output_file="emissions_temp_test.csv",
    log_level="debug"
)

tracker.start()

# simulate some work
print("Running workload...")
total = 0
for i in range(10_000_000):
    total += i

time.sleep(30)  # give monitor_power time to collect samples

emissions = tracker.stop()

# check results
print(f"\n--- Results ---")
print(f"Emissions: {emissions:.6f} kg CO2")
print(f"CPU temperature: {tracker.final_emissions_data.cpu_temperature:.1f}°C")
print(f"GPU temperature: {tracker.final_emissions_data.gpu_temperature:.1f}°C")

# verify CSV
df = pd.read_csv("emissions_temp_test.csv")
print(f"\n--- CSV columns ---")
print(df.columns.tolist())
print(f"\n--- Temperature values in CSV ---")
print(df[["cpu_temperature", "gpu_temperature"]])
