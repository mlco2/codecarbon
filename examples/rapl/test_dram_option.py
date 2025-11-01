#!/usr/bin/env python3
"""
Test script comparing CPU-only (package) vs CPU+DRAM power measurement.
This shows how include_dram=True gets closer to powerstat's readings.
"""
import subprocess
import time

from codecarbon.core.cpu import IntelRAPL
from codecarbon.core.units import Time

print("=" * 80)
print("Testing RAPL measurement: CPU-only vs CPU+DRAM")
print("=" * 80)

# Initialize both modes
print("\n1. CPU-only mode (default - most accurate for CPU power):")
rapl_cpu_only = IntelRAPL(include_dram=False)
rapl_cpu_only.start()

print("\n2. CPU+DRAM mode (matches powerstat's approach):")
rapl_with_dram = IntelRAPL(include_dram=True)
rapl_with_dram.start()

# Idle measurement
print("\n" + "=" * 80)
print("�� IDLE Measurement (3 seconds)")
print("=" * 80)
time.sleep(3)

details_cpu = rapl_cpu_only.get_cpu_details(Time.from_seconds(3))
details_dram = rapl_with_dram.get_cpu_details(Time.from_seconds(3))

cpu_only_power = sum(v for k, v in details_cpu.items() if "Power" in k)
cpu_dram_power = sum(v for k, v in details_dram.items() if "Power" in k)

print(f"CPU-only:     {cpu_only_power:6.2f} W")
print(f"CPU+DRAM:     {cpu_dram_power:6.2f} W")
print(f"DRAM contrib: {cpu_dram_power - cpu_only_power:6.2f} W")

# Stress test
print("\n" + "=" * 80)
print("🔥 STRESS TEST: Running 7z b (5 seconds)")
print("=" * 80)

# Start new measurement
rapl_cpu_only.start()
rapl_with_dram.start()

# Run 7z benchmark
proc = subprocess.Popen(
    ["7z", "b", "-mmt1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)
time.sleep(5)
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()

details_cpu = rapl_cpu_only.get_cpu_details(Time.from_seconds(5))
details_dram = rapl_with_dram.get_cpu_details(Time.from_seconds(5))

cpu_only_power_load = sum(v for k, v in details_cpu.items() if "Power" in k)
cpu_dram_power_load = sum(v for k, v in details_dram.items() if "Power" in k)

print(f"CPU-only:     {cpu_only_power_load:6.2f} W")
print(f"CPU+DRAM:     {cpu_dram_power_load:6.2f} W")
print(f"DRAM contrib: {cpu_dram_power_load - cpu_only_power_load:6.2f} W")

print("\n" + "=" * 80)
print("📈 Summary")
print("=" * 80)
print(
    f"CPU-only:  {cpu_only_power:5.1f}W idle → {cpu_only_power_load:5.1f}W load (+{cpu_only_power_load - cpu_only_power:5.1f}W)"
)
print(
    f"CPU+DRAM:  {cpu_dram_power:5.1f}W idle → {cpu_dram_power_load:5.1f}W load (+{cpu_dram_power_load - cpu_dram_power:5.1f}W)"
)

print("\n" + "=" * 80)
print("💡 Analysis")
print("=" * 80)
print(
    f"""
✓ CPU-only (default): Most accurate for CPU power tracking
  - Matches CPU TDP specs (15W for i7-7600U)
  - Best for comparing CPU performance/efficiency
  - Shown: {cpu_only_power_load:.1f}W under load

✓ CPU+DRAM (include_dram=True): Closer to powerstat
  - Includes memory power consumption
  - Better represents computing workload
  - Shown: {cpu_dram_power_load:.1f}W under load

⚠️  Note: Powerstat shows 40 - 80W because it also includes:
  - GPU/iGPU power
  - Chipset power
  - Display backlight
  - WiFi/Bluetooth
  - Other platform components

  RAPL can only measure CPU + DRAM on your system.
"""
)
