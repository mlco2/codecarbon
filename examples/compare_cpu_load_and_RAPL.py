"""
This script run a compute intensive task in parallel using multiprocessing.Pool
and compare the emissions measured by codecarbon using CPU load and RAPL mode.

It runs in less than 2 minutes on a powerful machine with 32 cores.

To run this script:
hatch run pip install tapo
export TAPO_USERNAME=XXX
export TAPO_PASSWORD=XXX
export IP_ADDRESS=192.168.0.XXX
hatch run python examples/compare_cpu_load_and_RAPL.py

"""

import asyncio
import os
import subprocess
import threading
import time
from threading import Thread

import pandas as pd
import psutil
from tapo import ApiClient

from codecarbon import EmissionsTracker
from codecarbon.external.hardware import CPU

measure_power_secs = 10
test_phase_duration = 60
test_phase_number = 10
measurements = []
task_name = ""
cpu_name = ""
log_level = "INFO"

# Read the credentials from the environment
tapo_username = os.getenv("TAPO_USERNAME")
tapo_password = os.getenv("TAPO_PASSWORD")
tapo_ip_address = os.getenv("IP_ADDRESS")

tapo_last_energy = 0
tapo_last_measurement = time.time()
tapo_client = None
if tapo_username:
    tapo_client = ApiClient(tapo_username, tapo_password)
else:
    print("WARNING : No tapo credentials found in the environment !!!")


async def read_tapo():
    global tapo_last_energy, tapo_last_measurement
    if not tapo_client:
        return 0, 0, 0
    try:

        device = await tapo_client.p110(tapo_ip_address)

        # device_info = await device.get_device_info()
        # print(f"Device info: {device_info.to_dict()}")

        device_usage = await device.get_device_usage()
        # print(f"Device usage: {device_usage.to_dict()}")
        tapo_energy = device_usage.power_usage.today
        # print(f"Energy: {tapo_energy} kWh")
        time_delta = time.time() - tapo_last_measurement
        tapo_last_measurement = time.time()
        delta_energy = tapo_energy - tapo_last_energy
        # print(f"Delta energy: {delta_energy} kWh")
        power = await device.get_current_power()

        # print(f"Current power: {power.to_dict()}")
        power = power.current_power
        # print(f"Power: {power} W")
        tapo_last_energy = tapo_energy
        return power, delta_energy, time_delta
    except Exception as e:
        print(f"Error reading tapo: {e}")
        return None, None, None


asyncio.run(read_tapo())


class MeasurementPoint:
    def __init__(self):
        self.task_name = ""
        self.cpu_name = ""
        self.timestamp = 0
        self.cores_used = 0
        self.cpu_load = 0
        self.temperature = 0
        self.cpu_freq = 0
        self.rapl_power = 0
        self.estimated_power = 0
        self.tapo_power = 0
        self.tapo_energy = 0
        self.tapo_time_delta = 0

    def __repr__(self):
        return (
            f"Cores: {self.cores_used}, Load: {self.cpu_load:.1f}%, "
            f"Temp: {self.temperature:.1f}°C, Freq: {self.cpu_freq:.1f}MHz, "
            f"RAPL: {self.rapl_power:.1f}W, Est: {self.estimated_power:.1f}W"
            f"Tapo: {self.tapo_power:.1f}W, {self.tapo_energy:.1f}kWh, {self.tapo_time_delta:.1f}s"
        )

    def to_dict(self):
        return {
            "task_name": self.task_name,
            "cpu_name": cpu_name,
            "timestamp": self.timestamp,
            "cores_used": self.cores_used,
            "cpu_load": self.cpu_load,
            "temperature": self.temperature,
            "cpu_freq": self.cpu_freq,
            "rapl_power": self.rapl_power,
            "estimated_power": self.estimated_power,
            "tapo_power": self.tapo_power,
            "tapo_energy": self.tapo_energy,
            "tapo_time_delta": self.tapo_time_delta,
        }


def collect_measurements(core_count):
    point = MeasurementPoint()
    point.task_name = task_name
    point.timestamp = time.time()
    point.cores_used = core_count
    point.cpu_load = psutil.cpu_percent(interval=0.1)

    # Get CPU temperature (average across cores)
    temps = psutil.sensors_temperatures()
    # print(f"Temps: {temps}")
    if "coretemp" in temps:
        point.temperature = sum(t.current for t in temps["coretemp"]) / len(
            temps["coretemp"]
        )
    # 'asus_wmi_sensors': [shwtemp(label='CPU Temperature', current=48.0
    if "asus_wmi_sensors" in temps:
        point.temperature = temps["asus_wmi_sensors"][0].current

    # Get CPU frequency (average across cores)
    freqs = psutil.cpu_freq(percpu=True)
    if freqs:
        point.cpu_freq = sum(f.current for f in freqs) / len(freqs)

    point.rapl_power = tracker_rapl._cpu_power.W
    point.estimated_power = tracker_cpu_load._cpu_power.W
    # Read tapo
    point.tapo_power, point.tapo_energy, point.tapo_time_delta = asyncio.run(
        read_tapo()
    )
    measurements.append(point)


def stress_ng(number_of_threads, test_phase_duration):
    """
    Call 'stress-ng --matrix <number_of_threads> --rapl -t 1m --verify'
    """
    subprocess.run(
        f"stress-ng --matrix {number_of_threads} --rapl -t {test_phase_duration} --verify",
        shell=True,
    )


def measurement_thread(core_count, stop_event):
    while not stop_event.is_set():
        collect_measurements(core_count)
        time.sleep(measure_power_secs / 2)


# Get the number of cores
cores = psutil.cpu_count()
cores_to_test = [i * (cores // test_phase_number) for i in range(test_phase_number + 1)]
cores_to_test.append(cores)
print("=" * 80)
print(f"We will run {len(cores_to_test)} tests for {test_phase_duration} seconds each.")
# print(f"Number of cores: {cores}, cores to test: {cores_to_test}")
print("=" * 80)
tracker_cpu_load = EmissionsTracker(
    measure_power_secs=measure_power_secs,
    force_mode_cpu_load=True,
    allow_multiple_runs=True,
    logger_preamble="CPU Load",
    log_level=log_level,
)
tracker_rapl = EmissionsTracker(
    measure_power_secs=measure_power_secs,
    allow_multiple_runs=True,
    logger_preamble="RAPL",
    log_level=log_level,
)

# Check if we could use RAPL
# print(f"Hardware: {tracker_rapl._hardware}")
for h in tracker_rapl._hardware:
    # print(f"{h=}")
    if isinstance(h, CPU):
        # print(f"{h._mode=}")
        # print(h._tracking_mode)  # machine / process
        if h._mode == "intel_rapl":
            cpu_name = h.get_model()
            break
else:
    raise ValueError("No RAPL mode found")

try:
    for core_to_run in cores_to_test:
        task_name = f"Stress-ng on {core_to_run} cores"
        tracker_cpu_load.start_task(task_name + " CPU Load")
        tracker_rapl.start_task(task_name + " RAPL")

        # Create and start measurement thread
        stop_measurement = threading.Event()
        measure_thread = Thread(
            target=measurement_thread, args=(core_to_run, stop_measurement)
        )
        measure_thread.start()

        # Run stress test
        if core_to_run == 0:
            # Just sleep, because, sending 0 to stress-ng mean "all cores" !
            time.sleep(test_phase_duration)
        else:
            stress_ng(core_to_run, test_phase_duration)

        # Stop measurement thread
        stop_measurement.set()
        measure_thread.join()

        cpu_load_data = tracker_cpu_load.stop_task()
        rapl_data = tracker_rapl.stop_task()
        print("=" * 80)
        print(measurements[-1].__dict__)
        print("=" * 80)

finally:
    # Stop measurement thread
    stop_measurement.set()
    measure_thread.join()


# Convert measurements to DataFrame
df = pd.DataFrame([m.to_dict() for m in measurements])
date = time.strftime("%Y-%m-%d")
df.to_csv(
    f"compare_cpu_load_and_RAPL-{cpu_name.replace(' ', '_')}-{date}.csv", index=False
)

# Calculate correlation between variables
print("\nCorrelations with RAPL power:")
correlations = df[["cpu_load", "temperature", "cpu_freq", "cores_used"]].corrwith(
    df["rapl_power"]
)
print(correlations)

# Compare estimated vs actual power
print("\nMean Absolute Error:")
mae = (df["estimated_power"] - df["rapl_power"]).abs().mean()
print(f"{mae:.2f} watts")

print("=" * 80)
for task_name, task in tracker_cpu_load._tasks.items():
    print(
        f"Emissions : {1000 * task.emissions_data.emissions:.0f} g CO₂ for task {task_name}"
    )
    print(
        f"\tEnergy : {1000 * task.emissions_data.cpu_energy:.1f} Wh {1000 * task.emissions_data.gpu_energy:.1f} Wh RAM:{1000 * task.emissions_data.ram_energy}Wh"
    )
    print(
        f"\tPower CPU:{task.emissions_data.cpu_power:.0f}W GPU:{task.emissions_data.gpu_power:.0f}W RAM:{task.emissions_data.ram_power:.0f}W"
        + f" during {task.emissions_data.duration:.1f} seconds."
    )
print("")
for task_name, task in tracker_rapl._tasks.items():
    print(
        f"Emissions : {1000 * task.emissions_data.emissions:.0f} g CO₂ for task {task_name}"
    )
    print(
        f"\tEnergy : {1000 * task.emissions_data.cpu_energy:.1f} Wh {1000 * task.emissions_data.gpu_energy:.1f} Wh RAM{1000 * task.emissions_data.ram_energy:.1f}Wh"
    )
    print(
        f"\tPower CPU:{task.emissions_data.cpu_power:.0f}W GPU:{task.emissions_data.gpu_power:.0f}W RAM:{task.emissions_data.ram_power:.0f}W"
        + f" during {task.emissions_data.duration:.1f} seconds."
    )
print("=" * 80)
"""
Lowest power at the plug when idle: 100 W
Peak power at the plug: 309 W
AMD Ryzen Threadripper 1950X 16-Core/32 threads Processor TDP: 180W
"""
