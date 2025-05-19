"""
Batch CPU Updater - Maintains all CPU files in sync
"""

import os
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS = {"User-Agent": "Mozilla/5.0 (CodeCarbon CPU Updater)"}
DELAY = 1
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_intel_cpus():
    """Fetch Intel CPUs and return DataFrame matching cpu_power.csv format"""
    base_url = "https://ark.intel.com"
    all_cpus = []

    print("Fetching Intel CPUs...")
    for page in tqdm(range(1, 15)):
        url = f"{base_url}/content/www/us/en/ark/search/featurefilter.html?productType=873&0_Processors=Production&PageSize=100&PageNumber={page}"

        try:
            time.sleep(DELAY)
            response = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            if not soup.select(".ark-product-list > li"):
                break

            for item in soup.select(".ark-product-list > li"):
                name = item.select_one(".result-title a").text.strip()
                specs = [spec.text.strip() for spec in item.select(".value")]

                tdp = re.search(r"(\d+)", specs[7]).group(1) if len(specs) > 7 else None
                cores = specs[1] if len(specs) > 1 else None

                all_cpus.append(
                    {
                        "name": name,
                        "tdp_watts": int(tdp) if tdp else None,
                        "cores": cores,
                        "manufacturer": "Intel",
                        "category": "Desktop" if "Desktop" in name else "Laptop",
                    }
                )

        except Exception as e:
            print(f"\nError on page {page}: {str(e)}")
            continue

    return pd.DataFrame(all_cpus)


def update_amd_files():
    """Update both AMD CSV files from TechPowerUp"""
    print("Updating AMD datasets...")
    url = "https://www.techpowerup.com/cpu-specs/?mfgr=amd"

    try:
        time.sleep(DELAY)
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        desktop_laptop = []
        server = []

        for row in tqdm(soup.select("#cputable tbody tr")):
            cols = row.select("td")
            if len(cols) < 6:
                continue

            name = cols[0].text.strip()
            tdp = cols[5].text.strip().replace("W", "")
            cores = cols[3].text.strip()

            cpu_data = {
                "name": name,
                "tdp_watts": int(tdp) if tdp.isdigit() else None,
                "cores": cores,
                "manufacturer": "AMD",
            }

            if "EPYC" in name or "Threadripper" in name:
                server.append(cpu_data)
            else:
                cpu_data["category"] = "Desktop" if "Desktop" in name else "Laptop"
                desktop_laptop.append(cpu_data)

        pd.DataFrame(desktop_laptop).to_csv(
            os.path.join(DATA_DIR, "AMD_CPU_desktop_laptop.csv"), index=False
        )
        pd.DataFrame(server).to_csv(
            os.path.join(DATA_DIR, "AMD_Server_Processor_Specifications.csv"),
            index=False,
        )

    except Exception as e:
        print(f"\nAMD update failed: {str(e)}")


def validate_updates():
    """Validate that files were created and contain sufficient data"""
    try:
        assert os.path.exists(os.path.join(DATA_DIR, "cpu_power.csv"))
        assert os.path.getsize(os.path.join(DATA_DIR, "cpu_power.csv")) > 100000
        assert os.path.exists(os.path.join(DATA_DIR, "AMD_CPU_desktop_laptop.csv"))
        assert os.path.exists(
            os.path.join(DATA_DIR, "AMD_Server_Processor_Specifications.csv")
        )
        print("Validation passed - all files look good!")
        return True
    except AssertionError as e:
        print(f"Validation failed: {str(e)}")
        return False


def update_all_cpus():
    """Update all CPU datasets"""
    update_amd_files()

    intel_df = fetch_intel_cpus()
    amd_df = pd.read_csv(os.path.join(DATA_DIR, "AMD_CPU_desktop_laptop.csv"))

    combined = pd.concat([intel_df, amd_df], ignore_index=True)
    combined.to_csv(os.path.join(DATA_DIR, "cpu_power.csv"), index=False)

    print("\nUpdate complete!")
    print(f"Total CPUs: {len(combined)}")
    print(f"Intel: {len(intel_df)} | AMD: {len(amd_df)}")

    validate_updates()


if __name__ == "__main__":
    update_all_cpus()
