# Estimating Carbon Offset Costs

!!! warning "CodeCarbon does not endorse any specific offset provider."

    This page explains how to turn CodeCarbon's emissions figure into an
    approximate price. It does not recommend offsetting, and the providers below
    are examples only. The CodeCarbon maintainers have reservations about
    offsetting ([#276](https://github.com/mlco2/codecarbon/issues/276)):

    - **Offsets often deliver much less than they claim.** A meta-analysis of
      2,346 crediting projects found that fewer than 16% of the credits issued
      matched real emission reductions[^probst]. For forest-protection (REDD+)
      projects, a study of 26 sites found that most did not significantly reduce
      deforestation. About 6% of the credits they expected to issue would match
      real reductions[^west].
    - **Some projects harm local communities.** Human Rights Watch documented a
      REDD+ project in Cambodia that ran for 31 months before consulting the
      Indigenous Chong people, and reported evictions from farmland[^hrw].
      Survival International raised similar concerns about a carbon project on
      Indigenous pastoralist land in northern Kenya[^survival]. The project
      operators dispute some of these findings.
    - **Offsetting does not make computing "clean".** A UN expert group says
      credits cannot count toward an organisation's own emission reductions[^hleg].
      Since September 2026, EU law has banned claims that a product is "climate
      neutral" when the claim rests on offsetting[^eu]. A purchased offset does
      not cancel the emissions CodeCarbon measured.

    Reduce your emissions first: run less, run on more efficient hardware, and
    run in regions and at times with lower carbon intensity. If you still choose
    to offset, read this page as a cost estimate, not as a way to become carbon
    neutral.

CodeCarbon tracks the carbon emissions of your code, but it does not calculate the monetary cost to offset those emissions. This guide shows you how to estimate offset costs using publicly available rates from carbon offset providers.

## Prerequisites

- CodeCarbon installed (`pip install codecarbon`)
- `pint` for unit conversion (`pip install pint`)

## Example Script

Below is a complete example that tracks emissions and estimates the cost to offset them using example rates from two providers (Cotap and Terrapass). They are listed only to illustrate the calculation.

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
```

## Notes

- Rates change over time. Check the current rate with the provider.
- The price of a credit says nothing about whether the reduction it claims is real. See the warning at the top of this page.
- For production use, consider calling provider APIs directly rather than hardcoding rates.

[^probst]: Probst, B. S. et al. (2024). *Systematic assessment of the achieved emission reductions of carbon crediting projects.* Nature Communications 15, 9562. [doi:10.1038/s41467-024-53645-z](https://doi.org/10.1038/s41467-024-53645-z)
[^west]: West, T. A. P. et al. (2023). *Action needed to make carbon offsets from forest conservation work for climate change mitigation.* Science 381(6660), 873–877. [doi:10.1126/science.ade3535](https://doi.org/10.1126/science.ade3535)
[^hrw]: Human Rights Watch (2024). [*Carbon Offsetting's Casualties: Violations of Chong Indigenous People's Rights in Cambodia's Southern Cardamom REDD+ Project.*](https://www.hrw.org/report/2024/02/28/carbon-offsettings-casualties/violations-chong-indigenous-peoples-rights)
[^survival]: Survival International (2023). [*Blood Carbon* (report on the Northern Kenya Rangelands Carbon Project)](https://assets.survivalinternational.org/documents/2466/Blood_Carbon_Report.pdf)
[^hleg]: UN High-Level Expert Group on the Net Zero Emissions Commitments of Non-State Entities (2022). [*Integrity Matters.*](https://www.un.org/en/climatechange/high-level-expert-group)
[^eu]: [Directive (EU) 2024/825](https://eur-lex.europa.eu/eli/dir/2024/825/oj) on empowering consumers for the green transition, applicable from 27 September 2026.
