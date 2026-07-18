# Product telemetry

CodeCarbon can send **optional private product telemetry** to help improve the library: hardware, environment, how the package is used, and per-run carbon/energy summaries. This is separate from sending **your** emissions to the [dashboard](cloud-api.md) with `save_to_api=True`.

## Telemetry vs your dashboard data

| | Product telemetry | Your emissions (`save_to_api`) |
|--|-------------------|--------------------------------|
| Purpose | Improve CodeCarbon (aggregate usage) | Your projects and experiments |
| Config | `telemetry_level`, `codecarbon telemetry` | `codecarbon config`, `experiment_id` |
| Default API target | Built-in telemetry project (private) | Your account / experiment |

You can use one without the other.

## Tiers

| `telemetry_level` | Name | When | Transport |
|-------------------|------|------|-----------|
| `disabled` | — | — | Nothing |
| `minimal` (default) | Private product telemetry | Each `stop()` | `POST /telemetry` (private) |
| `extensive` | Private telemetry + shared run summary | Each `stop()` | Same private `POST /telemetry` **and** `ApiClient` → `/emissions` |

Tier is resolved in this order:

1. **Tracker or CLI argument** — `EmissionsTracker(telemetry_level=...)` or `codecarbon monitor --telemetry-level ...`
2. **Config + environment** — `telemetry_level` in `.codecarbon.config`, then `CODECARBON_TELEMETRY_LEVEL` when both are set
3. **Default:** `minimal`

## Lifecycle

```text
EmissionsTracker.__init__  →  collect hardware/geo (no POST)
EmissionsTracker.stop()    →  minimal: private POST only  |  extensive: private POST + /emissions
```

If the run lasts less than one second, telemetry is not sent.

## Private telemetry — per run

Both tiers POST to `/telemetry` at each `stop()`. The server schema defines what each tier may include:

| Tier | Private `POST /telemetry` payload |
|------|-----------------------------------|
| `minimal` | Environment and hardware only (OS, Python, CPU/GPU/RAM, geo/cloud, CodeCarbon version) |
| `extensive` | Minimal fields **plus** run metrics, output methods, framework flags, usage diagnostics |

**Minimal** includes rounded coordinates (1 decimal), cloud region, and hardware metadata. It does **not** include run emissions, energy, duration, or framework flags.

**Extensive** adds run outcome (duration, emissions, energy, utilization), output methods, ML framework presence flags (booleans only, no package versions), CI/notebook/container/IDE hints, and integration context (`decorator_vs_context`: `library`, `cli_monitor`, or `offline_tracker`).

Private telemetry does **not** include project names, experiment ids, API keys, file paths, executable/host hashes, or survey demographics.

## `extensive` — additional public run summary

**Also** posts a **run emissions summary** to the shared CodeCarbon telemetry experiment via `ApiClient` (`/runs` then `/emissions`). Endpoint, API key, and experiment id come from `telemetry_api_url` / `telemetry_api_key` / `telemetry_experiment_id` (or `CODECARBON_TELEMETRY_*` env vars), then the built-in defaults. Dashboard `api_key` / `experiment_id` are **not** used for telemetry.

## Never collected

- Project name, experiment id, run id, API keys
- Source code, file paths, hostnames
- Exact GPS coordinates, executable/host fingerprints (not in the telemetry schema)
- Voluntary [user survey](https://docs.google.com/forms/d/e/1FAIpQLSeQ5Tu_rdrpDhBJvh5R1-_iB4Ld-kgh6iNMjgaMXa8AEVPxqA/viewform) demographics (role, industry, experience)

## Configure telemetry

### Config file

```ini
[codecarbon]
telemetry_level = minimal
```

### CLI

```bash
codecarbon telemetry set minimal
codecarbon telemetry status
codecarbon monitor --telemetry-level disabled -- python train.py
```

### Python

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(telemetry_level="minimal")
tracker.start()
# ...
tracker.stop()
```

## Opt out

```ini
[codecarbon]
telemetry_level = disabled
```

## First run without explicit configuration

If you never set `telemetry_level`, CodeCarbon uses `minimal` and logs a **one-time warning** per Python session. Set `telemetry_level` explicitly to silence it.

## Related

- [Configure CodeCarbon](configuration.md)
- [CLI reference](../reference/cli.md#codecarbon-telemetry)
- [Cloud API & dashboard](cloud-api.md)
