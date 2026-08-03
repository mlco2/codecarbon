"""
Print every channel exposed by the Windows Energy Meter Interface (EMI), and
the power each of them reports, to diagnose CPU power measurements.

Usage:
    python examples/emi_channels.py [duration_in_seconds]
"""

import sys
import time

from codecarbon.core import windows_emi


def main(duration: float = 5.0) -> int:
    print(f"windows_emi loaded from  : {windows_emi.__file__}")
    print(
        f"mirrored channel detection: {hasattr(windows_emi, 'find_mirrored_channels')}"
    )

    device_paths = windows_emi.list_emi_device_paths()
    print(f"energy meter device(s)   : {len(device_paths)}")
    if not device_paths:
        print("\nEMI is not available on this machine.")
        return 1

    channels = {}
    for device_path in device_paths:
        channels[device_path] = windows_emi._read_device_channels(device_path)
    selection = windows_emi.select_channels(list(channels.items()))
    for device_path, names in channels.items():
        selected = selection.get(device_path, [])
        print(f"\n{device_path}")
        for index, name in enumerate(names):
            state = "measured" if index in selected else "ignored"
            print(f"  [{index}] {name} ({state})")

    first = {
        path: windows_emi._read_device_measurements(path, len(names))
        for path, names in channels.items()
    }
    time.sleep(duration)
    second = {
        path: windows_emi._read_device_measurements(path, len(names))
        for path, names in channels.items()
    }

    print(f"\nPower measured over {duration} s:")
    total = 0.0
    for device_path, names in channels.items():
        selected = selection.get(device_path, [])
        for index, name in enumerate(names):
            energy_before, time_before = first[device_path][index]
            energy_after, time_after = second[device_path][index]
            delta_pwh = energy_after - energy_before
            delta_s = (time_after - time_before) * windows_emi.HNS_TO_S or duration
            watts = delta_pwh * windows_emi.PWH_TO_WH * 3600 / delta_s
            state = "measured" if index in selected else "ignored "
            print(
                f"  [{index}] {state} {name}: "
                f"counter {energy_before} -> {energy_after} = {watts:.2f} W"
            )
            if index in selected:
                total += watts

    print(f"\nSum of the measured channels: {total:.2f} W")
    print(
        "Compare it with the TDP of your CPU: a value far above it means the "
        "same energy is counted several times."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(float(sys.argv[1]) if len(sys.argv) > 1 else 5.0))
