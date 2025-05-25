"""
This script updates the CPU power data by reading from an Intel CPU data file,
cleaning the CPU names, and merging the data into an existing CPU power CSV file.
It ensures that the TDP values are numeric and updates existing entries or adds new ones.

hatch run python update_cpu_power.py

"""

import pandas as pd
import re


# Define file paths
intel_cpu_file = 'intel_cpu_data.csv'
cpu_power_file = 'cpu_power.csv'

# Read Intel CPU data
try:
    intel_df = pd.read_csv(intel_cpu_file)
except FileNotFoundError:
    print(f"Error: Intel CPU data file not found at {intel_cpu_file}")
    exit()

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
    name = name.strip()
    if not name.startswith("Intel "):
        name = "Intel " + name
    return name

intel_df['Name'] = intel_df['cpu_name'].apply(clean_intel_cpu_name)
intel_df = intel_df[['Name', 'tdp']].copy()
intel_df.rename(columns={'tdp': 'TDP'}, inplace=True)

# Ensure TDP is numeric, coercing errors to NaN (which will be dropped)
intel_df['TDP'] = pd.to_numeric(intel_df['TDP'], errors='coerce')
intel_df.dropna(subset=['Name', 'TDP'], inplace=True)
intel_df['TDP'] = intel_df['TDP'].astype(int)


# Read existing CPU power data
try:
    cpu_power_df = pd.read_csv(cpu_power_file)
except FileNotFoundError:
    print(f"Fatal Error: cpu_power.csv not found at {cpu_power_file}. Exiting.")
    exit(1)

# Ensure 'Name' column is string type for merging
cpu_power_df['Name'] = cpu_power_df['Name'].astype(str)
intel_df['Name'] = intel_df['Name'].astype(str)

# Remove duplicates from cpu_power_df before setting index
cpu_power_df.drop_duplicates(subset=['Name'], keep='first', inplace=True)
# Remove duplicates from intel_df before setting index to avoid issues if intel_cpu_data.csv also has dupes
intel_df.drop_duplicates(subset=['Name'], keep='first', inplace=True)

# Set 'Name' as index for easier update/merge
cpu_power_df.set_index('Name', inplace=True)
intel_df.set_index('Name', inplace=True)

# Update existing entries and add new ones
# For CPUs in intel_df, their TDP will overwrite existing TDP in cpu_power_df
# New CPUs from intel_df will be added
cpu_power_df.update(intel_df)
# Add CPUs from intel_df that were not in cpu_power_df
new_cpus = intel_df[~intel_df.index.isin(cpu_power_df.index)]
combined_df = pd.concat([cpu_power_df, new_cpus])


# Reset index and sort
combined_df.reset_index(inplace=True)
combined_df.sort_values(by='Name', inplace=True)

# Drop duplicates, keeping the first occurrence (which would be the updated/new one if there were any issues)
combined_df.drop_duplicates(subset=['Name'], keep='first', inplace=True)


# Save the updated dataframe
try:
    combined_df.to_csv(cpu_power_file, index=False)
    print(f"Successfully updated {cpu_power_file} with data from {intel_cpu_file}")
except Exception as e:
    print(f"Error writing to {cpu_power_file}: {e}")

print(f"Script finished. {cpu_power_file} has been updated.")
