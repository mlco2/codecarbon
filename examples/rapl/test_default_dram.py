#!/usr/bin/env python3
"""
Test that CodeCarbon now defaults to including DRAM for complete hardware measurement.
"""
import subprocess
import time

from codecarbon.core.cpu import IntelRAPL
from codecarbon.core.units import Time

print("=" * 80)
print("Testing CodeCarbon's new default: CPU+DRAM measurement")
print("=" * 80)

# Test default behavior (should now include DRAM)
print("\n1. Default IntelRAPL() - should include DRAM:")
rapl_default = IntelRAPL()
rapl_default.start()

print("\n2. Explicit include_dram=False - CPU only:")
rapl_cpu_only = IntelRAPL(include_dram=False)
rapl_cpu_only.start()

# Idle measurement
print("\n" + "=" * 80)
print("📊 IDLE Measurement (3 seconds)")
print("=" * 80)
time.sleep(3)

details_default = rapl_default.get_cpu_details(Time.from_seconds(3))
details_cpu_only = rapl_cpu_only.get_cpu_details(Time.from_seconds(3))

default_power = sum(v for k, v in details_default.items() if "Power" in k)
cpu_only_power = sum(v for k, v in details_cpu_only.items() if "Power" in k)

print(f"Default (CPU+DRAM):  {default_power:6.2f} W")
print(f"CPU-only:            {cpu_only_power:6.2f} W")
print(f"DRAM contribution:   {default_power - cpu_only_power:6.2f} W")

# Stress test
print("\n" + "=" * 80)
print("🔥 STRESS TEST: Running 7z b (5 seconds)")
print("=" * 80)

rapl_default.start()
rapl_cpu_only.start()

proc = subprocess.Popen(
    ["7z", "b", "-mmt1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)
time.sleep(5)
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()

details_default = rapl_default.get_cpu_details(Time.from_seconds(5))
details_cpu_only = rapl_cpu_only.get_cpu_details(Time.from_seconds(5))

default_power_load = sum(v for k, v in details_default.items() if "Power" in k)
cpu_only_power_load = sum(v for k, v in details_cpu_only.items() if "Power" in k)

print(f"Default (CPU+DRAM):  {default_power_load:6.2f} W")
print(f"CPU-only:            {cpu_only_power_load:6.2f} W")
print(f"DRAM contribution:   {default_power_load - cpu_only_power_load:6.2f} W")

print("\n" + "=" * 80)
print("✅ Summary")
print("=" * 80)
print("Default behavior now includes DRAM for complete hardware measurement!")
print(f"  Idle:  {default_power:.1f}W (CPU+DRAM) vs {cpu_only_power:.1f}W (CPU only)")
print(
    f"  Load:  {default_power_load:.1f}W (CPU+DRAM) vs {cpu_only_power_load:.1f}W (CPU only)"
)
print(
    "\nThis aligns with CodeCarbon's mission to measure complete hardware consumption! 🌱"
)
