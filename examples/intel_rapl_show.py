# This script demonstrates how to read power consumption using Intel RAPL (Running Average Power Limit) on Linux.
# It also list available power domains available on the system, like package (entire CPU), cores, uncore (RAM, cache), and platform
# The script can be used to monitor power consumption over time for a specific power domain
# The power consumption is read from the energy counter in microjoules and converted to watts

"""

Sample output for Intel(R) Core(TM) Ultra 7 265H
https://www.intel.com/content/www/us/en/products/sku/241750/intel-core-ultra-7-processor-265h-24m-cache-up-to-5-30-ghz/specifications.html
- Processor Base Power 28 W
- Maximum Turbo Power 115 W
- Minimum Assured Power 20 W



Available Power Domains:
[{'path': 'intel-rapl:1', 'name': 'psys', 'is_mmio': False}, {'path': 'intel-rapl:0:0', 'name': 'core', 'is_mmio': False}, {'path': 'intel-rapl-mmio:0', 'name': 'package-0', 'is_mmio': True}, {'path': 'intel-rapl:0:1', 'name': 'uncore', 'is_mmio': False}]
Starting Power Monitoring (deduplication: True):

Monitoring domains:
  - psys (intel-rapl:1) via MSR
  - core (intel-rapl:0:0) via MSR
  - package-0 (intel-rapl-mmio:0) via MMIO
  - uncore (intel-rapl:0:1) via MSR


Idle :
 - Domain 'psys' (MSR): 8.03 Watts
 - Domain 'core' (MSR): 1.51 Watts
 - Domain 'package-0' (MMIO): 4.61 Watts
 - Domain 'uncore' (MSR): 0.57 Watts
 - Total Power Consumption: 14.72 Watts

With `7z b` to load the CPU:

 - Domain 'psys' (MSR): 22.89 Watts
 - Domain 'core' (MSR): 14.49 Watts
 - Domain 'package-0' (MMIO): 18.51 Watts
 - Domain 'uncore' (MSR): 0.19 Watts
 - Total Power Consumption: 56.07 Watts

 psys (9.61W) ← Most comprehensive
├── package-0 (3.78W)
│   ├── core (0.84W) ← CPU cores only
│   └── uncore (0.21W) ← Memory controller, cache, iGPU
└── Other platform components (~5.8W)
    └── Chipset, PCIe, etc.

"""
import json
import os
import time


class RAPLDomainInspector:
    def __init__(self):
        self.rapl_base_path = "/sys/class/powercap/intel-rapl/subsystem"

    def inspect_rapl_domains(self):
        """
        Thoroughly inspect RAPL domains with detailed information
        """
        domain_details = {}

        try:
            # Iterate through all RAPL domains
            for domain_dir in os.listdir(self.rapl_base_path):
                print(domain_dir)
                if not (
                    domain_dir.startswith("intel-rapl:")
                    or domain_dir.startswith("intel-rapl-mmio:")
                ):
                    continue

                domain_path = os.path.join(self.rapl_base_path, domain_dir)
                domain_info = {
                    "domain_dir": domain_dir,
                    "files": {},
                    "subdomain_details": {},
                }

                # Check available files in the domain
                for file in os.listdir(domain_path):
                    try:
                        file_path = os.path.join(domain_path, file)
                        if os.path.isfile(file_path):
                            with open(file_path, "r") as f:
                                domain_info["files"][file] = f.read().strip()
                    except Exception as e:
                        domain_info["files"][file] = f"Error reading: {e}"

                # Check subdomains
                subdomains_path = os.path.join(domain_path, "subdomains")
                if os.path.exists(subdomains_path):
                    for subdomain in os.listdir(subdomains_path):
                        subdomain_full_path = os.path.join(subdomains_path, subdomain)
                        subdomain_info = {}

                        for file in os.listdir(subdomain_full_path):
                            try:
                                file_path = os.path.join(subdomain_full_path, file)
                                if os.path.isfile(file_path):
                                    with open(file_path, "r") as f:
                                        subdomain_info[file] = f.read().strip()
                            except Exception as e:
                                subdomain_info[file] = f"Error reading: {e}"

                        domain_info["subdomain_details"][subdomain] = subdomain_info

                domain_details[domain_dir] = domain_info

        except Exception as e:
            print(f"Error inspecting RAPL domains: {e}")

        return domain_details

    def identify_potential_ram_domains(self, domain_details):
        """
        Identify potential RAM-related domains based on name and characteristics

        Sample Detailed RAPL Domain Information:
        {
            "intel-rapl:1": {
                "domain_dir": "intel-rapl:1",
                "files": {
                "uevent": "",
                "energy_uj": "10359908363",
                "enabled": "0",
                "name": "package-0-die-1",
                "max_energy_range_uj": "65532610987"
                },
                "subdomain_details": {}
            },
            "intel-rapl:0": {
                "domain_dir": "intel-rapl:0",
                "files": {
                "uevent": "",
                "energy_uj": "10360237493",
                "enabled": "0",
                "name": "package-0-die-0",
                "max_energy_range_uj": "65532610987"
                },
                "subdomain_details": {}
            }
        }
        """
        potential_ram_domains = []

        for domain_name, domain_info in domain_details.items():
            # Check domain names that might indicate memory
            memory_indicators = [
                "dram",
                "uncore",
                "ram",
                "memory",
                "dimm",  # Common alternative identifiers
            ]

            is_potential_ram = any(
                indicator in domain_name.lower() for indicator in memory_indicators
            )

            if is_potential_ram:
                potential_ram_domains.append(
                    {"domain": domain_name, "details": domain_info}
                )
            is_potential_ram = any(
                indicator in domain_info["files"].get("name").lower()
                for indicator in memory_indicators
            )
            if is_potential_ram:
                potential_ram_domains.append(
                    {"domain": domain_name, "details": domain_info}
                )

        return potential_ram_domains


class IntelRAPL:
    def __init__(self):
        # Base path for RAPL power readings in sysfs
        self.rapl_base_path = "/sys/class/powercap/intel-rapl/subsystem"

    def list_power_domains(self, deduplicate=True):
        """
        List available RAPL power domains (including intel-rapl and intel-rapl-mmio)

        :param deduplicate: If True, avoid duplicate domains with same name, preferring MMIO
        :return: List of domain info dictionaries
        """
        all_domains = []
        try:
            for domain in os.listdir(self.rapl_base_path):
                if domain.startswith("intel-rapl:") or domain.startswith(
                    "intel-rapl-mmio:"
                ):
                    domain_info = {
                        "path": domain,
                        "name": "",
                        "is_mmio": domain.startswith("intel-rapl-mmio:"),
                    }
                    if os.path.exists(
                        os.path.join(self.rapl_base_path, domain, "name")
                    ):
                        with open(
                            os.path.join(self.rapl_base_path, domain, "name"), "r"
                        ) as f:
                            domain_info["name"] = f.read().strip()
                    all_domains.append(domain_info)

            # Deduplicate if requested
            if deduplicate:
                self.domains = self._deduplicate_domains(all_domains)
            else:
                self.domains = all_domains

            return self.domains
        except Exception as e:
            print(f"Error listing power domains: {e}")
            return []

    def _deduplicate_domains(self, domains):
        """
        Remove duplicate domains with the same name, preferring MMIO over MSR-based

        :param domains: List of domain info dictionaries
        :return: Deduplicated list
        """
        domain_map = {}

        for domain in domains:
            name = domain["name"]

            # If we haven't seen this name, or we're replacing MSR with MMIO
            if name not in domain_map or (
                domain["is_mmio"] and not domain_map[name]["is_mmio"]
            ):
                domain_map[name] = domain

        return list(domain_map.values())

    def read_power_consumption(self, domain=None, interval=1):
        """
        Read power consumption for a specific RAPL domain

        :param domain: Specific power domain to read (e.g., 'intel-rapl:0')
        :param interval: Time interval for power calculation
        :return: Power consumption in watts
        """
        if not domain:
            # If no domain specified, use the first available
            domains = self.list_power_domains()
            if not domains:
                print("No RAPL domains found")
                return None
            domain = domains[0]

        try:
            # Path to energy counter
            energy_path = os.path.join(
                self.rapl_base_path, domain.get("path"), "energy_uj"
            )

            # Read initial energy
            with open(energy_path, "r") as f:
                initial_energy = int(f.read().strip())

            # Wait for the specified interval
            time.sleep(interval)

            # Read energy again
            with open(energy_path, "r") as f:
                final_energy = int(f.read().strip())

            # Calculate power: (energy difference in microjoules) / (interval in seconds) / 1,000,000
            power = (final_energy - initial_energy) / (interval * 1_000_000)

            return power

        except Exception as e:
            print(f"Error reading power for {domain}: {e}")
            return None

    def monitor_power(self, interval=1, duration=10, deduplicate=True):
        """
        Monitor power consumption over time

        :param interval: Sampling interval in seconds
        :param duration: Total monitoring duration in seconds
        :param deduplicate: If True, avoid counting duplicate domains (e.g., same package via MSR and MMIO)
        """
        print(f"Starting Power Monitoring (deduplication: {deduplicate}):")
        if not self.domains:
            self.domains = self.list_power_domains(deduplicate=deduplicate)

        # Show which domains are being monitored
        print("\nMonitoring domains:")
        for domain in self.domains:
            interface = "MMIO" if domain.get("is_mmio") else "MSR"
            print(f"  - {domain.get('name')} ({domain.get('path')}) via {interface}")
        print()

        start_time = time.time()

        while time.time() - start_time < duration:
            total_power = 0
            for domain in self.domains:
                power = self.read_power_consumption(domain)
                if power is not None:
                    interface = "MMIO" if domain.get("is_mmio") else "MSR"
                    print(
                        f"Domain '{domain.get('name')}' ({interface}): {power:.2f} Watts"
                    )
                    total_power += power
            print(f"Total Power Consumption: {total_power:.2f} Watts\n")

            time.sleep(interval)


# Example usage
if __name__ == "__main__":
    inspector = RAPLDomainInspector()

    # Get detailed RAPL domain information
    domain_details = inspector.inspect_rapl_domains()

    # Pretty print full domain details
    print("Detailed RAPL Domain Information:")
    print(json.dumps(domain_details, indent=2))

    # Identify potential RAM domains
    potential_ram_domains = inspector.identify_potential_ram_domains(domain_details)

    print("\nPotential RAM Domains:")
    for domain in potential_ram_domains:
        print(f"Domain: {domain['domain']}")
        print("\tKey Files:")
        for file, value in domain["details"]["files"].items():
            print(f"\t  {file}: {value}")
    print("---")
    rapl = IntelRAPL()

    # List available power domains
    print("Available Power Domains:")
    print(rapl.list_power_domains())
    # Monitor power consumption
    rapl.monitor_power(interval=1, duration=5)
