import time
import math
import os
from codecarbon.emissions_tracker import EmissionsTracker # Assuming codecarbon is installable or in PYTHONPATH
from codecarbon.external.logger import logger, set_logger_level

# Set a verifiable experiment name for tracking if needed (optional)
os.environ["CODECARBON_EXPERIMENT_ID"] = "task-energy-test"

def cpu_intensive_task(duration_seconds):
    """A simple CPU-intensive task."""
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        _ = math.sqrt(time.time()) * math.factorial(100)

def main():
    set_logger_level("ERROR") # Keep CodeCarbon's own logs quiet unless error

    logger.info("Starting task energy consumption test script.")

    # Initialize EmissionsTracker
    # api_call_interval=2, measure_power_secs=1 : to encourage the bug if present
    # where _previous_emissions is updated by the live_out call too soon for task accounting.
    try:
        tracker = EmissionsTracker(
            project_name="TaskEnergyTest",
            measure_power_secs=1,
            api_call_interval=2, # This is the key to potentially trigger the old bug
            save_to_file=False,  # Don't write to emissions.csv for this test
            # log_level="DEBUG" # Use "DEBUG" if you want to see CodeCarbon's internal debug logs
        )
    except Exception as e:
        logger.error(f"Failed to initialize EmissionsTracker: {e}")
        print(f"TEST SCRIPT ERROR: Failed to initialize EmissionsTracker: {e}")
        return

    failing_rounds = []
    test_passed = True

    NUM_ROUNDS = 30 # Number of tasks to run
    TASK_DURATION_SEC = 4 # Duration of each CPU task

    logger.info(f"Tracker initialized. Running {NUM_ROUNDS} rounds of {TASK_DURATION_SEC}s tasks.")
    print(f"Tracker initialized. Running {NUM_ROUNDS} rounds of {TASK_DURATION_SEC}s tasks.")


    for i in range(NUM_ROUNDS):
        print(f"Starting round {i+1}/{NUM_ROUNDS}")
        try:
            tracker.start_task(f"CPU_Task_Round_{i+1}")
            cpu_intensive_task(TASK_DURATION_SEC)
            emissions_data = tracker.stop_task()

            if emissions_data:
                task_name = emissions_data.run_id # Using run_id as a stand-in for task_name if not directly available
                # In a real scenario, task_name might be part of emissions_data or retrieved via the task_id
                print(f"Round {i+1}: Task '{task_name}' (task_idx_{i+1}) completed. Duration: {emissions_data.duration:.4f}s, Energy: {emissions_data.energy_consumed:.6f} kWh, Emissions: {emissions_data.emissions:.6f} kg")

                # Check for the bug: zero energy for a non-trivial task duration
                if emissions_data.duration > 0.1 and emissions_data.energy_consumed == 0.0:
                    failing_rounds.append({
                        "round": i + 1,
                        "task_name": task_name,
                        "duration": emissions_data.duration,
                        "energy_consumed": emissions_data.energy_consumed,
                        "error": "Zero energy for non-trivial duration"
                    })
                    test_passed = False
            else:
                print(f"Round {i+1}: stop_task() did not return emissions_data.")
                failing_rounds.append({
                    "round": i + 1,
                    "task_name": f"CPU_Task_Round_{i+1}_NoData",
                    "error": "stop_task returned None"
                })
                test_passed = False

        except Exception as e:
            print(f"Round {i+1}: An error occurred: {e}")
            failing_rounds.append({
                "round": i + 1,
                "task_name": f"CPU_Task_Round_{i+1}_Exception",
                "error": str(e)
            })
            test_passed = False
            # Optionally, decide if one error should stop the whole test
            # break

        # Small delay to ensure measurements are distinct if needed,
        # and to let background scheduler of tracker run.
        time.sleep(1)

    tracker.stop() # Stop the main tracker

    if test_passed:
        print("TEST PASSED: No tasks with zero energy consumption detected for non-trivial durations.")
    else:
        print("TEST FAILED: Some tasks reported zero energy consumption or other errors.")
        print("Failing rounds details:")
        for detail in failing_rounds:
            # Ensure all fields are present with defaults for printing
            round_num = detail.get('round', 'N/A')
            task_name_val = detail.get('task_name', 'N/A')
            duration_val = detail.get('duration', float('nan')) # Use float('nan') for unavail num
            energy_val = detail.get('energy_consumed', float('nan'))
            error_val = detail.get('error', 'None')
            print(f"  - Round {round_num}: Task '{task_name_val}', "
                  f"Duration: {duration_val:.4f}s, Energy: {energy_val:.6f} kWh, "
                  f"Error: {error_val}")

if __name__ == "__main__":
    main()
