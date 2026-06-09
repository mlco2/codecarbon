#!/usr/bin/env python3
"""
Analyze what domains powerstat reads by examining all RAPL domains
and comparing with powerstat output.
"""

import os

print("=" * 80)
print("All available RAPL domains on your system:")
print("=" * 80)

# Find all RAPL domain directories
rapl_dirs = []
for base in ["/sys/class/powercap", "/sys/devices/virtual/powercap"]:
    if os.path.exists(base):
        for entry in os.listdir(base):
            if "intel-rapl" in entry:
                entry_path = os.path.join(base, entry)
                if os.path.isdir(entry_path):
                    for sub in os.listdir(entry_path):
                        if ":" in sub:
                            sub_path = os.path.join(entry_path, sub)
                            if os.path.isdir(sub_path):
                                rapl_dirs.append(sub_path)

rapl_dirs = sorted(set(rapl_dirs))

print(f"\nFound {len(rapl_dirs)} RAPL domains:\n")

for domain_dir in rapl_dirs:
    name_path = os.path.join(domain_dir, "name")
    energy_path = os.path.join(domain_dir, "energy_uj")

    name = "unknown"
    if os.path.exists(name_path):
        try:
            with open(name_path) as f:
                name = f.read().strip()
        except Exception:
            pass

    energy = "N/A"
    if os.path.exists(energy_path):
        try:
            with open(energy_path) as f:
                energy_uj = float(f.read().strip())
                energy = f"{energy_uj / 1e6:.2f} J"
        except Exception:
            energy = "Permission denied"

    provider = (
        "MSR" if "intel-rapl:" in domain_dir and "mmio" not in domain_dir else "MMIO"
    )

    print(
        f"  {os.path.basename(domain_dir):<25} | {name:<15} | {provider:<6} | {energy}"
    )

print("\n" + "=" * 80)
print("Powerstat approach (from powerstat.c analysis):")
print("=" * 80)
print(
    """
Powerstat reads ALL top-level domains and DEDUPLICATES by domain name:
  1. Scans /sys/class/powercap/intel-rapl:*
  2. Reads each domain's 'name' file
  3. Deduplicates domains with same name (prefers first found)
  4. SUMS all unique domains for total system power

This means powerstat likely reads:
  - package-0 (CPU package)
  - dram (memory)
  - psys (if unique, or skipped if duplicate)

Total = package-0 + dram + (other unique domains)
"""
)

print("\n" + "=" * 80)
print("Recommendation for CodeCarbon:")
print("=" * 80)
print(
    """
Option 1 (Current - CPU only):
  ✓ Read only package-0 domain
  ✓ Most accurate for CPU power measurement
  ✓ Matches CPU TDP specifications
  ✗ Doesn't match powerstat (which includes DRAM, etc.)

Option 2 (Match powerstat):
  ✓ Read package + dram domains (not psys)
  ✓ More complete system power picture
  ✓ Closer to powerstat readings
  ✗ Includes non-CPU components

Option 3 (Configurable):
  ✓ Let users choose via config parameter
  ✓ Default to package-0 (CPU only) for accuracy
  ✓ Allow 'all' mode to sum package+dram like powerstat
"""
)
