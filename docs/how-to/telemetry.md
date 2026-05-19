# Product telemetry

CodeCarbon can send **optional product telemetry** to help improve the library: which hardware and environments people run on, not what your code does. This is separate from sending **your** emissions to the [dashboard](cloud-api.md) with `save_to_api=True`.

## Telemetry vs your dashboard data

| | Product telemetry | Your emissions (`save_to_api`) |
|--|-------------------|--------------------------------|
| Purpose | Improve CodeCarbon (aggregate usage) | Your projects and experiments |
| Config | `telemetry_level`, `codecarbon telemetry` | `codecarbon config`, `experiment_id` |
| Default experiment | Public telemetry project (built-in defaults) | Your account / experiment |

You can use one without the other.

## Tiers

| `telemetry_level` | What happens |
|-------------------|--------------|
| `disabled` | No product telemetry |
| `minimal` (default) | **Tier 1** once per Python process: minimal hardware/environment metadata |
| `extensive` | Tier 1 + **Tier 2** on tracker `stop()`: one public emissions row (leaderboard-style) |

Tier is resolved in this order:

1. `EmissionsTracker(telemetry_level=...)` or `codecarbon monitor --telemetry-level ...`
2. `telemetry_level` in `.codecarbon.config` (local overrides global)
3. Default: `minimal`

Environment variables `CODECARBON_TELEMETRY` / `CODECARBON_TELEMETRY_LEVEL` count as “explicit” configuration (they suppress the one-time setup warning) but **do not** change the tier unless you also set `telemetry_level` in a config file or pass the tracker argument.

## Tier 1: what we collect (and what we do not)

Tier 1 is intentionally small. The client only builds a **minimal** payload; the API schema rejects “extensive” fields when `telemetry_level` is `minimal`.

### Sent at most once per process (if known)

Only non-empty values are included:

| Field | Description |
|-------|-------------|
| `timestamp` | UTC time of the send |
| `telemetry_level` | Always `minimal` for this tier |
| `os` | Platform string |
| `country_iso_code` | Country (e.g. from offline mode or geo) |
| `region` | Region / province |
| `cloud_provider` | Cloud provider name, if detected |
| `cloud_region` | Cloud region, if detected |
| `longitude`, `latitude` | Approximate location, if geo resolution ran |
| `cpu_count`, `cpu_physical_count`, `cpu_model` | CPU metadata |
| `gpu_count`, `gpu_model` | GPU metadata |
| `ram_total_size_gb` | Total RAM |
| `python_version` | Python version |
| `codecarbon_version` | Installed CodeCarbon version |

### Not sent in Tier 1

Tier 1 does **not** include:

- Emissions, energy, power, duration, or utilization
- Project name, experiment id, run id, or API keys
- Source code, file paths, hostnames, or user ids
- ML stack versions (PyTorch, TensorFlow, etc.)
- Output methods, tracking mode, or internal diagnostics
- Anything else defined as “extensive” in the telemetry schema

Tier 2 (`extensive`) adds a single **public** emissions summary via the same mechanism as `add_emission` to the shared telemetry experiment—not a full extensive telemetry document.

### Transport

- HTTP `POST` to `{telemetry_api_url}/telemetry`
- Best-effort: failures are logged and do not stop your tracker
- If the endpoint is not deployed yet, you may see a warning (HTTP 404)

## Configure telemetry

### Config file

```ini
[codecarbon]
telemetry_level = minimal
# Optional overrides (defaults point at the public telemetry API):
# telemetry_api_url = https://api.codecarbon.io
# telemetry_api_key = ...
# telemetry_experiment_id = ...
```

### CLI

```bash
# Interactive wizard (pick config file + tier)
codecarbon telemetry

# Set tier in config
codecarbon telemetry set disabled
codecarbon telemetry set minimal
codecarbon telemetry set extensive

# Show resolved tier (merged global + local config)
codecarbon telemetry show

# One-run override (does not write config)
codecarbon monitor --telemetry-level disabled -- python train.py
```

### Python

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(telemetry_level="disabled")
```

## Opt out

Set any of:

```ini
[codecarbon]
telemetry_level = disabled
```

```bash
codecarbon telemetry set disabled
```

```python
EmissionsTracker(telemetry_level="disabled")
```

## First run without explicit configuration

If you never set `telemetry_level`, CodeCarbon uses `minimal` and logs a **one-time warning** per Python session that Tier 1 will be sent. Set `telemetry_level` explicitly (config, CLI, or tracker argument) to silence it.

## Related

- [Configure CodeCarbon](configuration.md) — general `.codecarbon.config` hierarchy
- [CLI reference](../reference/cli.md#codecarbon-telemetry) — command flags
- [Cloud API & dashboard](cloud-api.md) — your own emissions data
