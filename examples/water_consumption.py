"""
Demonstrates the water consumption estimation.

CodeCarbon reports in `water_consumed` (litres) the sum of:
- the direct cooling water of the data center (`wue` parameter, L/kWh),
- the indirect water consumed to generate the electricity, estimated
  from the energy mix of the country where the machine runs.

Run it from the repo root:

    python examples/water_consumption.py
"""

import time

from codecarbon import EmissionsTracker


def cpu_load(seconds: float) -> None:
    end = time.time() + seconds
    x = 0
    while time.time() < end:
        x = (x + 1) % 1_000_000


def main() -> None:
    # Set wue to the Water Usage Effectiveness of your data center to also
    # count its cooling water; leave it at 0 outside a data center.
    tracker = EmissionsTracker(save_to_file=False, wue=0)

    tracker.start()
    try:
        cpu_load(5)
    finally:
        emissions = tracker.stop()

    data = tracker.final_emissions_data
    print(f"emissions: {emissions * 1000:.6f} g CO2eq")
    print(f"energy_consumed: {data.energy_consumed:.6f} kWh")
    print(f"water_consumed: {data.water_consumed:.6f} L")
    if data.energy_consumed:
        ratio = data.water_consumed / data.energy_consumed
        print(f"water intensity: {ratio:.2f} L/kWh in {data.country_name}")


if __name__ == "__main__":
    main()
