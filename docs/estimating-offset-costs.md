# Estimating Carbon Offset Costs

CodeCarbon tracks the carbon emissions of your code, but it does not calculate the monetary cost to offset those emissions. This guide shows you how to estimate offset costs using publicly available rates from carbon offset providers.

## Prerequisites

- CodeCarbon installed (`pip install codecarbon`)
- `pint` for unit conversion (`pip install pint`)

## Example Script

Below is a complete example that tracks emissions and estimates the cost to offset them via two different services (Cotap and Terrapass).

```python
import pint
from codecarbon import EmissionsTracker

# Setup unit registry
reg = pint.UnitRegistry()
reg.define('CO2 = []')
reg.define('dollar = []')
CO2_ton = reg.CO2 * reg.metric_ton
CO2_kg = reg.CO2 * reg.kg
CO2_pound = reg.CO2 * reg.pound

# Track emissions
tracker = EmissionsTracker()
tracker.start()

# Your GPU/CPU intensive code here
# ...

emissions_kg = tracker.stop()  # returns emissions in kg

# Convert to pint quantity
emissions = emissions_kg * CO2_kg

# Offset provider rates (as of 2022)
# These should be updated periodically or checked directly with providers.
co2_offset_costs = {
    'terrapass': (100.75 * reg.dollars) / (20_191 * CO2_pound).to(CO2_ton),
    'cotap': (15 * reg.dollars) / (1 * CO2_ton),
}

# Choose a provider
service = 'cotap'
dollar_per_co2ton = co2_offset_costs[service]

# Calculate cost
cost_to_offset = (emissions * dollar_per_co2ton).to_base_units()
print(f"Estimated offset cost via {service}: ${cost_to_offset.magnitude:.2f}")


Notes

· Rates are subject to change. Always verify current rates with the provider.
· This guide is for educational purposes. CodeCarbon does not endorse any specific offset provider.
· For production use, consider calling provider APIs directly rather than hardcoding rates.
