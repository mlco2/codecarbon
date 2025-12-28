#!/usr/bin/env python3
"""
Simple test script to verify GPU load monitoring functionality.
This script will run a simple workload and check if GPU utilization is being tracked.
"""

import time

from codecarbon import EmissionsTracker


def main():
    print("Starting GPU load monitoring test...")
    print("=" * 60)

    # Initialize the tracker
    tracker = EmissionsTracker(
        project_name="gpu_load_test",
        measure_power_secs=2,
        save_to_file=True,
        output_file="test_gpu_emissions.csv",
    )

    # Start tracking
    tracker.start()
    print("Tracker started. Running for 10 seconds...")

    # Run for a short duration to collect some metrics
    time.sleep(10)

    # Stop tracking
    emissions = tracker.stop()

    print("=" * 60)
    print("Test completed!")
    print(f"Total emissions: {emissions:.6f} kg CO2")

    # Check if GPU utilization was tracked
    if hasattr(tracker, "final_emissions_data"):
        data = tracker.final_emissions_data
        print(f"GPU utilization: {data.gpu_utilization_percent:.2f}%")
        print(f"CPU utilization: {data.cpu_utilization_percent:.2f}%")
        print(f"RAM utilization: {data.ram_utilization_percent:.2f}%")

        if data.gpu_utilization_percent > 0:
            print("\n✓ GPU utilization tracking is working!")
        else:
            print("\n⚠ GPU utilization is 0% (may not have GPU or no GPU workload)")

    print("\nCheck test_gpu_emissions.csv for detailed results.")


if __name__ == "__main__":
    main()
