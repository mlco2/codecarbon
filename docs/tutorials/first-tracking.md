# Your First Emissions Tracking

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mlco2/codecarbon/blob/master/docs/tutorials/first-tracking.ipynb)

This tutorial walks you through tracking your first carbon emissions with CodeCarbon.
By the end, you will have:

1. Installed CodeCarbon
2. Tracked emissions from a simple computation
3. Inspected the results

---

## Step 1: Install CodeCarbon


```python
!pip install codecarbon
```

## Step 2: Track emissions from a computation

The simplest way to use CodeCarbon is as a **context manager**. Everything inside the `with` block is tracked.


```python
from codecarbon import EmissionsTracker

with EmissionsTracker(project_name="my-first-tracking") as tracker:
    # Simulate some computation
    total = 0
    for i in range(10_000_000):
        total += i

print(f"Computation result: {total}")
```

## Step 3: Inspect the results

CodeCarbon saved the emissions data to a CSV file. Let's take a look:


```python
import pandas as pd

df = pd.read_csv("emissions.csv")
df[["project_name", "duration", "emissions", "emissions_rate", "cpu_power", "ram_power", "energy_consumed"]]
```

You can also access the emissions data directly from the tracker object:


```python
print(f"Total emissions: {tracker.final_emissions * 1000:.4f} g CO2eq")
print(f"Duration: {tracker.final_emissions_data.duration:.2f} seconds")
print(f"Energy consumed: {tracker.final_emissions_data.energy_consumed:.6f} kWh")
```

## What's next?

- [Configure CodeCarbon](../how-to/configuration.md) with config files, environment variables, or script parameters
- Learn about [CLI tracking](cli.md) to monitor without code changes
- Explore all [Python API options](python-api.md) (decorators, explicit objects, offline mode)
- See the full [API Reference](../reference/api.md) for all configuration parameters
- Try the [CodeCarbon Workshop notebook](https://github.com/mlco2/codecarbon/blob/master/examples/notebooks/codecarbon_workshop.ipynb) for a comprehensive hands-on experience
