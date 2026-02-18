#!/usr/bin/env python3
"""
Test script to compare package-0 (CPU only) vs psys (platform/system) RAPL domains.
This helps determine which domain matches powerstat's measurements.
"""
import time

print("=" * 80)
print("Comparing RAPL domains: package-0 (CPU) vs psys (platform)")
print("=" * 80)

# Read both domains
package_path = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"
psys_path = "/sys/class/powercap/intel-rapl/intel-rapl:1/energy_uj"


def read_energy(path):
    """Read energy in microjoules"""
    with open(path, "r") as f:
        return float(f.read().strip())


def measure_power(duration=1.0):
    """Measure power over a duration in seconds"""
    package_start = read_energy(package_path)
    psys_start = read_energy(psys_path)

    time.sleep(duration)

    package_end = read_energy(package_path)
    psys_end = read_energy(psys_path)

    # Calculate power in Watts (µJ/s -> W)
    package_power = (package_end - package_start) / duration / 1_000_000
    psys_power = (psys_end - psys_start) / duration / 1_000_000

    return package_power, psys_power


print("\n--- IDLE measurement (5 seconds) ---")
package_idle, psys_idle = measure_power(5.0)
print(f"package-0 (CPU only):     {package_idle:6.2f} W")
print(f"psys (full platform):     {psys_idle:6.2f} W")
print(f"Difference (non-CPU):     {psys_idle - package_idle:6.2f} W")

print("\n--- Generating CPU load for 5 seconds ---")
start = time.time()
counter = 0
while time.time() - start < 5:
    counter += sum(range(100000))

package_load, psys_load = measure_power(5.0)
print(f"package-0 (CPU only):     {package_load:6.2f} W")
print(f"psys (full platform):     {psys_load:6.2f} W")
print(f"Difference (non-CPU):     {psys_load - package_load:6.2f} W")

print("\n--- Power increase under load ---")
print(f"package-0 increase:       {package_load - package_idle:6.2f} W")
print(f"psys increase:            {psys_load - psys_idle:6.2f} W")

print("\n" + "=" * 80)
print("Analysis:")
print("=" * 80)
print("• package-0 shows CPU power only (~15W TDP for i7-7600U)")
print("• psys shows total platform power (CPU + GPU + chipset + etc)")
print("• powerstat likely reads psys or sums all domains")
print("• Your CPU TDP: 15W, max turbo: 25W")
print(f"• Measured package-0: {package_idle:.1f}W idle, {package_load:.1f}W load")
print(f"• Measured psys: {psys_idle:.1f}W idle, {psys_load:.1f}W load")
print("=" * 80)
