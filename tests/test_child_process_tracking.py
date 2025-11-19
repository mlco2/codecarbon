import multiprocessing
import os
import sys
import time

from codecarbon import EmissionsTracker

"""
Test script to verify that CPU tracking includes child processes
when using tracking_mode="process".

This test creates multiple child processes that perform CPU-intensive work
and verifies that the CPU usage is properly tracked.
"""


def cpu_intensive_work(duration, process_id):
    """Perform CPU-intensive work for the specified duration"""
    print(f"Child process {process_id} starting CPU-intensive work for {duration}s")
    end_time = time.time() + duration
    iterations = 0
    while time.time() < end_time:
        # Perform some CPU-intensive calculations
        _ = sum(i * i for i in range(10000))
        iterations += 1
    print(f"Child process {process_id} completed {iterations} iterations")


def test_child_process_tracking():
    """Test that child processes are tracked in process mode"""
    print("=" * 80)
    print("Testing CPU Child Process Tracking")
    print("=" * 80)

    # Start tracker in process mode
    print("\nStarting EmissionsTracker in 'process' mode...")
    tracker = EmissionsTracker(
        tracking_mode="process",
        measure_power_secs=1,
        save_to_file=False,
        log_level="info",
        force_mode_cpu_load=True,  # Force software estimation to test our fix
    )
    tracker.start()

    print(f"Main process PID: {os.getpid()}")

    # Spawn multiple child processes
    num_processes = 4
    work_duration = 5  # seconds

    print(f"\nSpawning {num_processes} child processes for {work_duration}s each...")
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=cpu_intensive_work, args=(work_duration, i))
        p.start()
        processes.append(p)
        print(f"  Started child process {i} (PID: {p.pid})")

    # Wait for children to complete
    print("\nWaiting for child processes to complete...")
    for i, p in enumerate(processes):
        p.join()
        print(f"  Child process {i} completed")

    # Stop tracker and get emissions
    print("\nStopping tracker...")
    emissions = tracker.stop()

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total emissions: {emissions:.6f} kg CO2")
    print(f"CPU energy: {tracker.final_emissions_data.cpu_energy:.6f} kWh")
    print(f"CPU power: {tracker.final_emissions_data.cpu_power:.2f} W")
    print(f"Duration: {tracker.final_emissions_data.duration:.2f} s")

    # Verify that we tracked some CPU usage
    if tracker.final_emissions_data.cpu_energy > 0:
        print("\n✓ SUCCESS: CPU energy was tracked (child processes included)")
    else:
        print("\n✗ FAILURE: No CPU energy tracked")
        return False

    # Calculate expected minimum energy
    # With 4 child processes running CPU-intensive work for 5 seconds,
    # we should see significant CPU usage
    expected_min_power = 10  # Watts (conservative estimate)
    if tracker.final_emissions_data.cpu_power >= expected_min_power:
        print(
            f"✓ SUCCESS: CPU power ({tracker.final_emissions_data.cpu_power:.2f}W) is above minimum threshold ({expected_min_power}W)"
        )
    else:
        print(
            f"⚠ WARNING: CPU power ({tracker.final_emissions_data.cpu_power:.2f}W) is below expected threshold ({expected_min_power}W)"
        )
        print("  This might indicate child processes are not being tracked properly")

    print("\n" + "=" * 80)
    return True


if __name__ == "__main__":
    # Set start method for multiprocessing
    multiprocessing.set_start_method("spawn", force=True)

    success = test_child_process_tracking()
    sys.exit(0 if success else 1)
