# This script demonstrates how to read power consumption using Intel RAPL (Running Average Power Limit) on Linux.
# It also list available power domains available on the system, like package (entire CPU), cores, uncore (RAM, cache), and platform
# The script can be used to monitor power consumption over time for a specific power domain
# The power consumption is read from the energy counter in microjoules and converted to watts

import json
import os
import time


class RAPLDomainInspector:
    def __init__(self):
        self.rapl_base_path = "/sys/class/powercap/intel-rapl"

    def inspect_rapl_domains(self):
        """
        Thoroughly inspect RAPL domains with detailed information
        """
        domain_details = {}

        try:
            # Iterate through all RAPL domains
            for domain_dir in os.listdir(self.rapl_base_path):
                if not domain_dir.startswith("intel-rapl:"):
                    continue

                domain_path = os.path.join(self.rapl_base_path, domain_dir)
                domain_info = {"name": domain_dir, "files": {}, "subdomain_details": {}}

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
                "name": "intel-rapl:1",
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
                "name": "intel-rapl:0",
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

        return potential_ram_domains


class IntelRAPL:
    def __init__(self):
        # Base path for RAPL power readings in sysfs
        self.rapl_base_path = "/sys/class/powercap/intel-rapl"

    def list_power_domains(self):
        """
        List available RAPL power domains
        """
        domains = []
        try:
            for domain in os.listdir(self.rapl_base_path):
                if domain.startswith("intel-rapl:"):
                    domains.append(domain)
            return domains
        except Exception as e:
            print(f"Error listing power domains: {e}")
            return []

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
            energy_path = os.path.join(self.rapl_base_path, domain, "energy_uj")

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

    def monitor_power(self, interval=1, duration=10):
        """
        Monitor power consumption over time

        :param interval: Sampling interval in seconds
        :param duration: Total monitoring duration in seconds
        """
        print("Starting Power Monitoring:")
        start_time = time.time()

        while time.time() - start_time < duration:
            power = self.read_power_consumption()
            if power is not None:
                print(f"Power Consumption: {power:.2f} Watts")

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
        print("Key Files:")
        for file, value in domain["details"]["files"].items():
            print(f"  {file}: {value}")
        print("---")
    rapl = IntelRAPL()

    # List available power domains
    print("Available Power Domains:")

    # Monitor power consumption
    rapl.monitor_power(interval=1, duration=5)
