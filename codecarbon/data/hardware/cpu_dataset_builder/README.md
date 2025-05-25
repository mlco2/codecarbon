# How to update the CPU database

To update the CPU database, you have to run:

```bash
cd codecarbon/data/hardware/cpu_dataset_builder
hatch run pip install playwright beautifulsoup4
hatch run python intel_cpu_scrapper.py
hatch run python amd_cpu_scrapper.py
hatch run python merge_scrapped_cpu_power.py
```

Then commit the changes to the CSV files.

CodeCarbon only use the `cpu_power.csv` file, but we keep the other files for reference and to allow someone else to use them if needed.
