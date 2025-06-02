import os
import time

from codecarbon import EmissionsTracker

# Ensure you have your CODECARBON_API_TOKEN if you use the API
# or configure offline mode as needed.
# For simplicity, this script assumes offline mode if no API key is found,
# but you should adjust it to your actual CodeCarbon setup.

API_KEY = os.environ.get("CODECARBON_API_TOKEN")
OFFLINE_MODE = API_KEY is None

if OFFLINE_MODE:
    print("Running in OFFLINE mode as CODECARBON_API_TOKEN is not set.")
    # For offline, you might need to specify country_iso_code, etc.
    # Adjust these parameters as per your setup or config file
    tracker = EmissionsTracker(
        project_name="ZeroEnergyTestLoop",
        measure_power_secs=1,  # Or your desired interval
        tracking_mode="process",
        # country_iso_code="USA", # Example for offline
        # region="california",    # Example for offline
        log_level="debug",  # Set to debug to get all codecarbon logs + our new ones
    )
else:
    print(
        f"Running in ONLINE mode with API Key: {API_KEY[:5]}..."
    )  # Print part of key for confirmation
    tracker = EmissionsTracker(
        project_name="ZeroEnergyTestLoop",
        measure_power_secs=1,  # Or your desired interval
        tracking_mode="process",
        api_key=API_KEY,
        log_level="debug",  # Set to debug to get all codecarbon logs + our new ones
    )


def busy_task(duration_secs=4):
    print(f"  Task: Starting busy work for ~{duration_secs} seconds...")
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < duration_secs:
        # Simulate some CPU work
        # for _ in range(100000): # Adjust complexity as needed
        #     pass
        time.sleep(2)
    end_time = time.perf_counter()
    print(f"  Task: Finished busy work in {end_time - start_time:.2f} seconds.")


max_rounds = 100  # Safety break for the loop

print("Starting tracking loop. Will stop if energy_consumed is 0.0 for a task.")

try:
    for current_round in range(max_rounds):
        print(f"Round {current_round + 1}:")
        task_name = f"round_{current_round + 1}_task"

        tracker.start_task(task_name)
        print(f"  Tracker: Started task '{task_name}'")

        busy_task(duration_secs=4)  # Simulate work for about 4 seconds

        emissions_data = tracker.stop_task()
        print(f"  Tracker: Stopped task '{task_name}'")

        if emissions_data:
            print(f"  EmissionsData for {task_name}:")
            print(f"    Duration: {emissions_data.duration:.4f}s")
            print(f"    CPU Energy: {emissions_data.cpu_energy:.6f} kWh")
            print(f"    GPU Energy: {emissions_data.gpu_energy:.6f} kWh")
            print(f"    RAM Energy: {emissions_data.ram_energy:.6f} kWh")
            print(
                f"    Total Energy Consumed: {emissions_data.energy_consumed:.6f} kWh"
            )
            print(f"    Emissions: {emissions_data.emissions:.6f} kg CO2eq")

            if emissions_data.energy_consumed == 0.0:
                print("###########################################################")
                print(
                    f"INFO: energy_consumed is 0.0 in round {current_round + 1}. Stopping loop."
                )
                print("###########################################################")
                break
        else:
            print(f"  WARNING: tracker.stop_task() returned None for {task_name}")

        # Small pause between rounds, can be adjusted or removed
        time.sleep(1)

    else:  # Executed if the loop completes without break
        print(
            f"Loop completed {max_rounds} rounds without encountering zero energy consumption."
        )

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    print("Stopping global tracker (if it was started implicitly or if needed).")
    # tracker.stop() # Call stop() if you started the main tracker with tracker.start() explicitly.
    # For tasks, usually stop_task is enough unless you have a global start().
    # If the tracker is only used for tasks like this, explicit stop() might not be needed
    # or could even cause issues if not started.
    # However, it's good practice if you use the tracker in a broader scope.
    # For this script, since we initialize tracker but don't call tracker.start(),
    # calling tracker.stop() might error if it wasn't implicitly started.
    # The EmissionsTracker's __exit__ method (if used with `with`) handles stop.
    # If running tasks like this, the library should handle shutdown on exit or via stop_task effects.
    print("Script finished.")
