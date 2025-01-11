"""
This script run a compute intensive task in parallel using multiprocessing.Pool
and compare the emissions measured by codecarbon using CPU load and RAPL mode.

It runs in less than 2 minutes on a powerful machine with 32 cores.

To run this script:
sudo apt install stress-ng
hatch run pip install tapo
export TAPO_USERNAME=XXX
export TAPO_PASSWORD=XXX
export IP_ADDRESS=192.168.0.XXX
hatch run python examples/compare_cpu_load_and_RAPL.py

"""

import asyncio
import os
import subprocess
import time
from threading import Thread

import pandas as pd
import psutil

try:
    from tapo import ApiClient
except ImportError:
    print("WARNING : No tapo module found !!!")

from codecarbon import EmissionsTracker
from codecarbon.external.hardware import CPU, MODE_CPU_LOAD

measure_power_secs = 10
test_phase_duration = 30
test_phase_number = 10
measurements = []
task_name = ""
cpu_name = ""
log_level = "DEBUG"

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

# all_cores: Mean we load all the cores at a given load level
LOAD_ALL_CORES = "all_cores"
# some_cores: Mean we load some cores at full load
LOAD_SOME_CORES = "some_cores"


# Verify that stress-ng is installed
def check_stress_ng_installed():
    try:
        subprocess.run(
            ["stress-ng", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("stress-ng is installed.")
    except subprocess.CalledProcessError:
        print(
            "ERROR stress-ng is not installed. Please install it using 'sudo apt install stress-ng'."
        )
        exit(1)


check_stress_ng_installed()


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
        self.load_type = ""
        self.cpu_name = ""
        self.timestamp = 0
        self.cores_used = 0
        self.cpu_load = 0
        self.temperature = 0
        self.cpu_freq = 0
        self.rapl_power = 0
        self.rapl_energy = 0
        self.estimated_power = 0
        self.estimated_energy = 0
        self.tapo_power = 0
        self.tapo_energy = 0
        self.tapo_time_delta = 0
        self.duration = 0

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
            "load_type": self.load_type,
            "cpu_name": cpu_name,
            "timestamp": self.timestamp,
            "cores_used": self.cores_used,
            "cpu_load": self.cpu_load,
            "temperature": self.temperature,
            "cpu_freq": self.cpu_freq,
            "rapl_power": self.rapl_power,
            "rapl_energy": self.rapl_energy,
            "estimated_power": self.estimated_power,
            "estimated_energy": self.estimated_energy,
            "tapo_power": self.tapo_power,
            "tapo_energy": self.tapo_energy,
            "tapo_time_delta": self.tapo_time_delta,
            "duration": self.duration,
        }


def collect_measurements(expected_load, load_type):
    print(f"Collecting measurements for {expected_load}% load.")
    if load_type == LOAD_SOME_CORES:
        cores_used = expected_load
    else:
        cores_used = get_cpu_cores()
    point = MeasurementPoint()
    point.task_name = task_name
    point.load_type = load_type
    point.timestamp = time.time()
    point.cores_used = cores_used
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

    # point.rapl_power = tracker_rapl._cpu_power.W
    # point.estimated_power = tracker_cpu_load._cpu_power.W
    # Read tapo
    point.tapo_power, point.tapo_energy, point.tapo_time_delta = asyncio.run(
        read_tapo()
    )
    measurements.append(point)


def get_cpu_cores():
    """
    Get the number of CPU cores
    """
    return psutil.cpu_count()


def get_list_of_cores_to_test(nb):
    cores_to_test = [0]
    indice = nb / test_phase_number
    for i in range(test_phase_number):
        cores_to_test.append(int(indice * (i + 1)))
    return sorted(list(set(cores_to_test)))


# assert get_list_of_cores_to_test(32) == [0, 3, 6, 9, 12, 16, 19, 22, 25, 28, 32]


def stress_ng(load_type, test_phase_duration, expected_load):
    """
    Call 'stress-ng --matrix <number_of_threads> --rapl -t 1m --verify'
    """
    if load_type == LOAD_SOME_CORES:
        subprocess.run(
            f"stress-ng  --cpu-method float64 --cpu {expected_load} --rapl -t {test_phase_duration} --verify",
            shell=True,
        )
    elif load_type == LOAD_ALL_CORES:
        subprocess.run(
            f"stress-ng  --cpu-method float64 --cpu 0 --rapl -l {expected_load} -t {test_phase_duration} --verify",
            shell=True,
        )
    else:
        raise ValueError(f"Unknown load type: {load_type}")


def measurement_thread(core_count, load_type):
    # We do a mesurement in the middle of the task
    time.sleep(test_phase_duration / 2)
    collect_measurements(core_count, load_type)


# Get the number of cores
print("=" * 80)
print(f"We will run {test_phase_number} tests for {test_phase_duration} seconds each.")
# print(f"Number of cores: {cores}, cores to test: {cores_to_test}")
print("=" * 80)
tracker_cpu_load = EmissionsTracker(
    measure_power_secs=measure_power_secs,
    force_mode_cpu_load=True,
    allow_multiple_runs=True,
    logger_preamble="CPU Load",
    log_level=log_level,
    save_to_file=False,
)
tracker_rapl = EmissionsTracker(
    measure_power_secs=measure_power_secs,
    allow_multiple_runs=True,
    logger_preamble="RAPL",
    log_level=log_level,
    save_to_file=False,
)

# Check if we could use RAPL
# print(f"Hardware: {tracker_rapl._hardware}")
for h in tracker_rapl._hardware:
    # print(f"{h=}")
    if isinstance(h, CPU):
        # print(f"{h._mode=}")
        # print(h._tracking_mode)  # machine / process
        if h._mode == "intel_rapl":
            # Set global CPU name
            cpu_name = h.get_model()
            break
else:
    raise ValueError("No RAPL mode found")

# Check we have the TDP
for h in tracker_cpu_load._hardware:
    if isinstance(h, CPU):
        if h._mode == MODE_CPU_LOAD:
            break
else:
    raise ValueError("No TDP found for your CPU.")


def one_test(expected_load, load_type):
    try:
        task_name = f"Stress-ng for {expected_load}% load on {load_type}"
        tracker_cpu_load.start_task(task_name + " CPU Load")
        tracker_rapl.start_task(task_name + " RAPL")

        # Create and start measurement thread
        measure_thread = Thread(
            target=measurement_thread, args=(expected_load, load_type)
        )
        measure_thread.start()

        # Run stress test
        if expected_load < 1:
            # Just sleep, because, sending 0 to stress-ng mean "all cores" !
            time.sleep(test_phase_duration)
        else:
            stress_ng(load_type, test_phase_duration, expected_load)

        # Stop measurement thread
        # measure_thread.join()

        cpu_load_data = tracker_cpu_load.stop_task()
        rapl_data = tracker_rapl.stop_task()
        point = measurements[-1]
        point.rapl_power = rapl_data.cpu_power
        point.rapl_energy = rapl_data.cpu_energy
        point.estimated_power = cpu_load_data.cpu_power
        point.estimated_energy = cpu_load_data.cpu_energy
        point.duration = rapl_data.duration

        print("=" * 80)
        print(measurements[-1].__dict__)
        print("=" * 80)
    finally:
        # Stop measurement thread
        measure_thread.join()


def measure_power(load_type):
    if load_type == LOAD_SOME_CORES:
        expected_loads = get_list_of_cores_to_test(get_cpu_cores())
        for expected_load in expected_loads:
            one_test(expected_load, load_type)
    elif load_type == LOAD_ALL_CORES:
        for i in range(test_phase_number + 1):
            expected_load = i * 10
            one_test(expected_load, load_type)


def data_output(load_type, measurements):
    # Convert measurements to DataFrame
    df = pd.DataFrame([m.to_dict() for m in measurements])
    print(df)
    date = time.strftime("%Y-%m-%d")
    df.to_csv(
        f"compare_cpu_load_and_RAPL-{load_type}-{cpu_name.replace(' ', '_')}-{date}.csv",
        index=False,
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

    tasks = []

    for task_name, task in tracker_cpu_load._tasks.items():
        tasks.append(
            {
                "task_name": task_name,
                "emissions_cpu_load": task.emissions_data.emissions,
                "cpu_energy_cpu_load": task.emissions_data.cpu_energy,
                "gpu_energy_cpu_load": task.emissions_data.gpu_energy,
                "ram_energy_cpu_load": task.emissions_data.ram_energy,
                "cpu_power_cpu_load": task.emissions_data.cpu_power,
                "gpu_power_cpu_load": task.emissions_data.gpu_power,
                "ram_power_cpu_load": task.emissions_data.ram_power,
                "duration_cpu_load": task.emissions_data.duration,
            }
        )
    print("")
    task_id = 0
    for _, task in tracker_rapl._tasks.items():
        tasks[task_id]["emissions_rapl"] = task.emissions_data.emissions
        tasks[task_id]["cpu_energy_rapl"] = task.emissions_data.cpu_energy
        tasks[task_id]["gpu_energy_rapl"] = task.emissions_data.gpu_energy
        tasks[task_id]["ram_energy_rapl"] = task.emissions_data.ram_energy
        tasks[task_id]["cpu_power_rapl"] = task.emissions_data.cpu_power
        tasks[task_id]["gpu_power_rapl"] = task.emissions_data.gpu_power
        tasks[task_id]["ram_power_rapl"] = task.emissions_data.ram_power
        tasks[task_id]["duration_rapl"] = task.emissions_data.duration
        task_id += 1
    df_tasks = pd.DataFrame(tasks)
    df_tasks.to_csv(
        f"compare_cpu_load_and_RAPL-{load_type}-{cpu_name.replace(' ', '_')}-{date}-tasks.csv",
        index=False,
    )


"""
Lowest power at the plug when idle: 100 W
Peak power at the plug: 309 W
AMD Ryzen Threadripper 1950X 16-Core/32 threads Processor TDP: 180W
"""


if __name__ == "__main__":
    results = []
    for load_type in [LOAD_ALL_CORES, LOAD_SOME_CORES]:
        measurements = []
        measure_power(load_type)
        results.append(measurements.copy())

    for result, load_type in zip(results, [LOAD_ALL_CORES, LOAD_SOME_CORES]):
        data_output(load_type, result)
