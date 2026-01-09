import time
import csv
from pathlib import Path

from codecarbon import EmissionsTracker


def cpu_load(seconds) -> None:
    end = time.time() + seconds
    x = 0
    while time.time() < end:
        x = (x + 1) % 1_000_000


def last_row(csv_path: Path) -> dict:
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = None
        for row in reader:
            pass
    if row is None:
        raise RuntimeError("emissions.csv exists but has no data rows.")
    return row


def main() -> None:
    csv_path = Path("emissions.csv")
    if csv_path.exists():
        csv_path.unlink()  # avoid reading an old file

    tracker = EmissionsTracker(save_to_file=True, save_to_api=False)

    tracker.start()
    cpu_load(2.0)
    tracker.stop()

    if not csv_path.exists():
        raise RuntimeError("emissions.csv was not created.")

    row = last_row(csv_path)

    if "water_consumed" not in row or row["water_consumed"] == "":
        raise RuntimeError("Missing or empty 'water_consumed' in emissions.csv.")

    water = float(row["water_consumed"])
    print(f"water_consumed: {water:.6f} L")

    if "energy_consumed" in row and row["energy_consumed"] != "":
        energy = float(row["energy_consumed"])
        print(f"energy_consumed: {energy:.6f} kWh")
        if energy > 0:
            print(f"water_per_kWh: {water / energy:.6f} L/kWh")

    print("OK")


if __name__ == "__main__":
    main()
