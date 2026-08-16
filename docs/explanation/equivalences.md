# Equivalences

The `carbonboard` dashboard translates a project's emissions into three
everyday comparisons. They are presentation aids, not part of the measurement:
nothing in the CSV output, the API payload or the emissions calculation depends
on them.

All three factors live in
[`codecarbon/viz/data.py`](https://github.com/mlco2/codecarbon/blob/master/codecarbon/viz/data.py)
and are used by `viz/carbonboard.py` and `viz/carbonboard_on_api.py`.

| Comparison | Factor | Applied as | Source |
|---|---|---|---|
| Car travel | **0.409 kg CO₂e per mile** | `emissions_kg / 0.409` → miles driven (`Data.get_car_miles`) | US EPA |
| Television | **0.097 kg CO₂ per hour** | `emissions_kg / 0.097` → hours of TV (`Data.get_tv_time`) | unsourced in code |
| US household | **160.58 kg CO₂ per week** | `emissions_kg / 160.58 × 100` → % of a household-week (`Data.get_household_fraction`) | US EPA |

## How each factor is derived

The derivations below are reproduced from the docstrings in `viz/data.py`; they
are the only justification the code carries.

**Car — 0.409 kg CO₂e/mile** (`KG_CO2E_PER_MILE`)

```text
8.89 × 10⁻³ metric tons CO₂ per gallon of gasoline
  × 1 / 22.0 miles per gallon (car/truck average)
  × 1 CO₂, CH₄ and N₂O / 0.988 CO₂
= 4.09 × 10⁻⁴ metric tons CO₂e per mile
= 0.409 kg CO₂e per mile
```

This is the US EPA passenger-vehicle figure, so it reflects the US vehicle
fleet and US fuel. It is not a European or global average, and the unit is
**miles**, not kilometres.

**Television — 0.097 kg CO₂/hour** (`KG_CO2_PER_TV_HOUR`)

Described in the code only as the ratio for "a 32-inch LCD flat screen TV".
**No source, screen power, or grid intensity is given in the code**, so the
figure cannot be reproduced from what ships in the repository. Treat it as an
illustrative round number rather than a defensible factor.

**US household — 160.58 kg CO₂/week** (`KG_CO2_PER_HOUSEHOLD_WEEK`)

```text
5.734 t CO₂  electricity
+ 2.06  t CO₂  natural gas
+ 0.26  t CO₂  liquid petroleum gas
+ 0.30  t CO₂  fuel oil
= 8.35 t CO₂ per home per year
÷ 52 weeks
= 160.58 kg CO₂ per week
```

Again a US EPA figure for total *home energy* use — heating fuels included, not
electricity alone — and specific to an average US home.

## Caveats

- All three factors are US-centric averages. A reader outside the US should
  expect the comparison to be directionally useful and quantitatively off.
- The factors are hardcoded and not versioned against a dated source release,
  so they drift out of date silently as the underlying EPA figures are revised.
- They are applied to the emissions total *after* the estimation chain
  described in the [methodology](methodology.md), so every uncertainty in that
  chain carries through unchanged.

If you need a comparison you can defend, compute it yourself from the
`emissions` column of the [CSV output](../reference/output.md) using a factor
you can cite.
