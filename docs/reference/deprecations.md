# Deprecations and migrations

Everything in CodeCarbon that still works but is on its way out: when it was
deprecated, when it is scheduled to be removed, and what to use instead.

User-visible changes per release are on the
[GitHub releases page](https://github.com/mlco2/codecarbon/releases).

| Deprecated | Since | Removal | Replacement |
|---|---|---|---|
| `codecarbon[viz-legacy]` extra | 3.3.0 | 4.0.0 | `codecarbon[carbonboard]` |
| `save_to_file`, `save_to_api`, `save_to_logger`, `save_to_prometheus`, `save_to_logfire` parameters | 3.2.8 | Not scheduled | `output_methods=[...]` |
| `co2_signal_api_token` parameter and config key | 3.1.1 | Not scheduled | `electricitymaps_api_token` |

## `viz-legacy` extra

The old Dash-based dashboard extra is replaced by `carbonboard`.

```bash
# before
pip install codecarbon[viz-legacy]

# after
pip install codecarbon[carbonboard]
```

See [Visualize Emissions](../how-to/visualize.md) for how to run it.

## `save_to_*` parameters

Passing any `save_to_*` flag raises a `DeprecationWarning`. Pass the outputs you want
as a list instead.

```python
# mktestdocs: skip
# before
EmissionsTracker(save_to_file=True, save_to_logger=True)

# after
from codecarbon.output_methods.base_output import OutputMethod

EmissionsTracker(output_methods=[OutputMethod.CSV, OutputMethod.LOGGER])
```

See [Output Formats](output.md) for the full list of output methods.

## `co2_signal_api_token`

The CO2 Signal API became part of Electricity Maps. The old parameter and config key
still work and are read as a fallback, but they log a warning.

```python
# mktestdocs: skip
# before
EmissionsTracker(co2_signal_api_token="...")

# after
EmissionsTracker(electricitymaps_api_token="...")
```

```ini
# .codecarbon.config — before
[codecarbon]
co2_signal_api_token = ...

# .codecarbon.config — after
[codecarbon]
electricitymaps_api_token = ...
```

## For maintainers

This table is the checklist for the next major release: everything with a removal
version scheduled for it must be removed, and every "Not scheduled" row should get a
decision before the release is cut.
