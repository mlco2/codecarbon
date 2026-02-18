#!/usr/bin/env python3
"""
Test script to compare RAPL domains (package-0 vs psys) with reliable CPU stress using 7z b.
This helps diagnose why RAPL readings might not match powerstat measurements.
"""
import os
import subprocess
import time

print("=" * 80)
print("RAPL Domain Comparison: package-0 (CPU) vs psys (platform)")
print("=" * 80)

# Check if 7z is available
try:
    result = subprocess.run(["7z"], capture_output=True, timeout=1)
    has_7z = True
except (FileNotFoundError, subprocess.TimeoutExpired):
    print("\n⚠️  WARNING: 7z not found. Install with: sudo apt install p7zip-full")
    print("Falling back to Python-based CPU stress (less reliable)\n")
    has_7z = False

# Read both domains
package_path = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"
psys_path = "/sys/class/powercap/intel-rapl/intel-rapl:1/energy_uj"


def read_energy(path):
    """Read energy in microjoules"""
    with open(path, "r") as f:
        return float(f.read().strip())


def read_max_energy(path):
    """Read max energy range in microjoules"""
    max_path = path.replace("energy_uj", "max_energy_range_uj")
    if os.path.exists(max_path):
        with open(max_path, "r") as f:
            return float(f.read().strip())
    return None


def measure_power(duration=3.0):
    """Measure power over a duration in seconds, handling wraparound"""
    package_start = read_energy(package_path)
    psys_start = read_energy(psys_path)
    package_max = read_max_energy(package_path)
    psys_max = read_max_energy(psys_path)

    time.sleep(duration)

    package_end = read_energy(package_path)
    psys_end = read_energy(psys_path)

    # Handle wraparound (following powerstat approach)
    package_delta = package_end - package_start
    if package_delta < 0:
        print("  [Wraparound detected in package-0: adding max_energy_range]")
        if package_max is not None:
            package_delta += package_max
        else:
            print(
                "  [Warning: package-0 max_energy_range unknown; cannot correct wraparound]"
            )

    psys_delta = psys_end - psys_start
    if psys_delta < 0:
        print("  [Wraparound detected in psys: adding max_energy_range]")
        if psys_max is not None:
            psys_delta += psys_max
        else:
            print(
                "  [Warning: psys max_energy_range unknown; cannot correct wraparound]"
            )

    # Calculate power in Watts (µJ/duration -> W)
    package_power = package_delta / duration / 1_000_000
    psys_power = psys_delta / duration / 1_000_000

    return package_power, psys_power, package_delta, psys_delta


print("\n📊 Domain Information:")
print(f"  package-0: {package_path}")
print(f"  psys:      {psys_path}")
package_max = read_max_energy(package_path)
psys_max = read_max_energy(psys_path)
if package_max:
    print(
        f"  package-0 max range: {package_max / 1e9:.2f} kJ ({package_max / 3.6e12:.2f} kWh)"
    )
if psys_max:
    print(
        f"  psys max range:      {psys_max / 1e9:.2f} kJ ({psys_max / 3.6e12:.2f} kWh)"
    )

# Idle measurement
print("\n" + "=" * 80)
print("1️⃣  IDLE Measurement (5 seconds)")
print("=" * 80)
package_idle, psys_idle, pkg_idle_delta, psys_idle_delta = measure_power(5.0)
print(
    f"✓ package-0 (CPU only):     {package_idle:6.2f} W  (delta: {pkg_idle_delta / 1e6:.4f} J)"
)
print(
    f"✓ psys (full platform):     {psys_idle:6.2f} W  (delta: {psys_idle_delta / 1e6:.4f} J)"
)
print(f"  Difference (non-CPU):     {psys_idle - package_idle:6.2f} W")

# CPU stress test
print("\n" + "=" * 80)
if has_7z:
    print("2️⃣  STRESS TEST: Running 7z b (5 seconds)")
    print("=" * 80)
    print("Starting 7z benchmark...")

    # Start power measurement
    package_start = read_energy(package_path)
    psys_start = read_energy(psys_path)
    start_time = time.time()

    # Run 7z benchmark (single-threaded for 5 seconds)
    proc = subprocess.Popen(
        ["7z", "b", "-mmt1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Let it run for 5 seconds
    time.sleep(5.0)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

    # Calculate actual duration
    duration = time.time() - start_time

    # Read final energy
    package_end = read_energy(package_path)
    psys_end = read_energy(psys_path)

    # Calculate power with wraparound handling
    package_delta = package_end - package_start
    if package_delta < 0:
        print("  [Wraparound detected in package-0]")
        package_max_temp = read_max_energy(package_path)
        if package_max_temp is not None:
            package_delta += package_max_temp
        else:
            print(
                "  [Warning: package-0 max_energy_range unknown; cannot correct wraparound]"
            )

    psys_delta = psys_end - psys_start
    if psys_delta < 0:
        print("  [Wraparound detected in psys]")
        psys_max_temp = read_max_energy(psys_path)
        if psys_max_temp is not None:
            psys_delta += psys_max_temp
        else:
            print(
                "  [Warning: psys max_energy_range unknown; cannot correct wraparound]"
            )

    package_load = package_delta / duration / 1_000_000
    psys_load = psys_delta / duration / 1_000_000

    print(
        f"✓ package-0 (CPU only):     {package_load:6.2f} W  (delta: {package_delta / 1e6:.4f} J)"
    )
    print(
        f"✓ psys (full platform):     {psys_load:6.2f} W  (delta: {psys_delta / 1e6:.4f} J)"
    )
    print(f"  Difference (non-CPU):     {psys_load - package_load:6.2f} W")
else:
    print("2️⃣  STRESS TEST: Python CPU load (5 seconds)")
    print("=" * 80)
    print("Starting CPU stress...")

    package_start = read_energy(package_path)
    psys_start = read_energy(psys_path)
    start_time = time.time()

    # Python-based CPU stress
    counter = 0
    while time.time() - start_time < 5:
        counter += sum(range(100000))

    duration = time.time() - start_time

    package_end = read_energy(package_path)
    psys_end = read_energy(psys_path)

    package_delta = package_end - package_start
    if package_delta < 0:
        package_max_temp = read_max_energy(package_path)
        if package_max_temp is not None:
            package_delta += package_max_temp
        else:
            print(
                "  [Warning: package-0 max_energy_range unknown; cannot correct wraparound]"
            )

    psys_delta = psys_end - psys_start
    if psys_delta < 0:
        psys_max_temp = read_max_energy(psys_path)
        if psys_max_temp is not None:
            psys_delta += psys_max_temp
        else:
            print(
                "  [Warning: psys max_energy_range unknown; cannot correct wraparound]"
            )

    package_load = package_delta / duration / 1_000_000
    psys_load = psys_delta / duration / 1_000_000

    print(
        f"✓ package-0 (CPU only):     {package_load:6.2f} W  (delta: {package_delta / 1e6:.4f} J)"
    )
    print(
        f"✓ psys (full platform):     {psys_load:6.2f} W  (delta: {psys_delta / 1e6:.4f} J)"
    )
    print(f"  Difference (non-CPU):     {psys_load - package_load:6.2f} W")

# Analysis
print("\n" + "=" * 80)
print("📈 Power Change Analysis")
print("=" * 80)
print(
    f"package-0 increase:       {package_load - package_idle:+6.2f} W  ({((package_load / package_idle - 1) * 100):+.1f}%)"
)
print(
    f"psys increase:            {psys_load - psys_idle:+6.2f} W  ({((psys_load / psys_idle - 1) * 100):+.1f}%)"
)

print("\n" + "=" * 80)
print("🔍 Diagnosis")
print("=" * 80)
print("• Your CPU: Intel Core i7-7600U @ 2.80GHz")
print("• TDP: 15W nominal, 25W configurable")
print(f"• package-0 (CPU only):  {package_idle:.1f}W idle → {package_load:.1f}W load")
print(f"• psys (full platform):  {psys_idle:.1f}W idle → {psys_load:.1f}W load")

if package_load - package_idle < 2:
    print("\n⚠️  WARNING: package-0 shows minimal increase (<2W) under load!")
    print("   This suggests RAPL counter update issues on your Intel laptop.")

if psys_load - psys_idle < 5:
    print("\n⚠️  WARNING: psys shows minimal increase (<5W) under load!")
    print("   This suggests RAPL counter update issues on your Intel laptop.")

print("\n💡 Recommendation:")
if psys_load - psys_idle > package_load - package_idle:
    print(
        f"   → psys shows better response to load (+{psys_load - psys_idle:.1f}W vs +{package_load - package_idle:.1f}W)"
    )
    print("   → CodeCarbon should use psys for your system")
else:
    print(
        f"   → package-0 shows better response to load (+{package_load - package_idle:.1f}W vs +{psys_load - psys_idle:.1f}W)"
    )
    print("   → CodeCarbon should use package-0 for your system")

print("\n📊 Compare with powerstat:")
print("   Run: sudo powerstat -R 1 10")
print("   If powerstat shows 40-80W under load but RAPL shows <30W,")
print("   this indicates a known Intel RAPL firmware/kernel issue.")
print("=" * 80)
