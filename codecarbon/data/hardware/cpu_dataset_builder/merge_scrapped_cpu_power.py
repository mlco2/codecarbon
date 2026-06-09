"""
This script updates the CPU power data by reading from Intel and AMD CPU data file,
cleaning the CPU names, and merging the data into an existing CPU power CSV file.
It ensures that the TDP values are numeric and updates existing entries or adds new ones.

cd codecarbon/data/hardware/cpu_dataset_builder
uv run python merge_scrapped_cpu_power.py

"""

import re

import pandas as pd

# Define file paths
intel_cpu_file = "intel_cpu_ark_dataset.csv"
amd_desktop_cpu_file = "amd_cpu_desktop_dataset.csv"
amd_server_cpu_file = "amd_cpu_server_dataset.csv"
cpu_power_file = "../cpu_power.csv"

# Read Intel CPU data
try:
    intel_df = pd.read_csv(intel_cpu_file)
    amd_desktop_df = pd.read_csv(amd_desktop_cpu_file)
    amd_server_df = pd.read_csv(amd_server_cpu_file)
except FileNotFoundError as e:
    print(f"FATAL Error: Data file not found {e}")
    exit(1)


# Clean Intel CPU names and select relevant columns
def clean_intel_cpu_name(name):
    if pd.isna(name):
        return None
    name = re.sub(r"®", "", name)
    name = name.replace(r"(R)", "")
    name = name.replace(r"(TM)", "")
    name = re.sub(r" Processor", "", name)
    name = re.sub(r" Coprocessor", "", name)
    name = re.sub(r"™", "", name)
    name = re.sub(r" with.*", "", name)
    name = name.strip()
    if not name.startswith("Intel "):
        name = "Intel " + name
    return name


if not intel_df.empty:
    intel_df["Name"] = intel_df["cpu_name"].apply(clean_intel_cpu_name)
    intel_df = intel_df[["Name", "tdp"]].copy()
    intel_df.rename(columns={"tdp": "TDP"}, inplace=True)
else:
    intel_df = pd.DataFrame(columns=["Name", "TDP"])


# Clean AMD CPU names
def clean_amd_cpu_name(name):
    if pd.isna(name):
        return None
    name = str(name)  # Ensure name is a string
    name = re.sub(r"®", "", name)
    name = name.replace(r"(R)", "")
    name = name.replace(r"(TM)", "")
    name = re.sub(r" Processor", "", name)
    name = re.sub(r"™", "", name)
    name = re.sub(r" with.*", "", name)
    name = name.strip()
    if not name.startswith("AMD "):
        name = "AMD " + name
    return name


def extract_tdp_value(tdp_str):
    if pd.isna(tdp_str):
        return None
    tdp_str = str(tdp_str).replace("W", "").strip()
    # If it's a range like "15-54", take the upper value
    if "-" in tdp_str:
        try:
            return float(tdp_str.split("-")[-1])
        except ValueError:
            return None
    try:
        return float(tdp_str)
    except ValueError:
        return None


amd_desktop_df["Name"] = amd_desktop_df["Name"].apply(clean_amd_cpu_name)
amd_desktop_df.rename(columns={"Default TDP": "TDP"}, inplace=True)
amd_desktop_df = amd_desktop_df[["Name", "TDP"]].copy()
amd_desktop_df["TDP"] = amd_desktop_df["TDP"].apply(extract_tdp_value)

amd_server_df["Name"] = amd_server_df["Name"].apply(clean_amd_cpu_name)
amd_server_df = amd_server_df[["Name", "Default TDP"]].copy()
amd_server_df.rename(columns={"Default TDP": "TDP"}, inplace=True)
amd_server_df["TDP"] = amd_server_df["TDP"].apply(extract_tdp_value)

# Concatenate all CPU data
all_cpus_df = pd.concat([intel_df, amd_desktop_df, amd_server_df], ignore_index=True)

print(
    f"Total CPUs found: {len(all_cpus_df)} using Intel {len(intel_df)}, AMD Desktop {len(amd_desktop_df)}, and AMD Server {len(amd_server_df)} datasets."
)

# Ensure TDP is numeric, coercing errors to NaN (which will be dropped)
all_cpus_df["TDP"] = pd.to_numeric(all_cpus_df["TDP"], errors="coerce")
all_cpus_df.dropna(subset=["Name", "TDP"], inplace=True)
all_cpus_df["TDP"] = all_cpus_df["TDP"].astype(int)


# Read existing CPU power data
try:
    cpu_power_df = pd.read_csv(cpu_power_file)
except FileNotFoundError:
    print(f"FATAL ERROR: cpu_power.csv not found at {cpu_power_file}. Exiting.")
    exit(1)


# Ensure 'Name' column is string type for merging
cpu_power_df["Name"] = cpu_power_df["Name"].astype(str)
all_cpus_df["Name"] = all_cpus_df["Name"].astype(str)

# Remove duplicates from cpu_power_df before setting index
cpu_power_df.drop_duplicates(subset=["Name"], keep="first", inplace=True)
# Remove duplicates from all_cpus_df before setting index to avoid issues if source data also has dupes
all_cpus_df.drop_duplicates(subset=["Name"], keep="first", inplace=True)

# Set 'Name' as index for easier update/merge
cpu_power_df.set_index("Name", inplace=True)
all_cpus_df.set_index("Name", inplace=True)

# Update existing entries and add new ones
# For CPUs in all_cpus_df, their TDP will overwrite existing TDP in cpu_power_df
# New CPUs from all_cpus_df will be added
cpu_power_df.update(all_cpus_df)
# Add CPUs from all_cpus_df that were not in cpu_power_df
new_cpus = all_cpus_df[~all_cpus_df.index.isin(cpu_power_df.index)]
combined_df = pd.concat([cpu_power_df, new_cpus])


# Reset index and sort
combined_df.reset_index(inplace=True)
combined_df.sort_values(by="Name", inplace=True, kind="mergesort")

# Drop duplicates, keeping the first occurrence (which would be the updated/new one if there were any issues)
combined_df.drop_duplicates(subset=["Name"], keep="first", inplace=True)


# Save the updated dataframe
try:
    combined_df.to_csv(cpu_power_file, index=False)
    print(
        f"Successfully updated {cpu_power_file} with data from Intel and AMD CPU datasets."
    )
except Exception as e:
    print(f"Error writing to {cpu_power_file}: {e}")

print(f"Script finished. {cpu_power_file} has been updated.")
