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
| `minimal` | Private product telemetry | Each `stop()` | `POST /telemetry` (private) |
| `extensive` | Private telemetry + shared run summary | Each `stop()` | Same private `POST /telemetry` **and** `ApiClient` → `/emissions` |

Tier is resolved in this order:

1. **Tracker or CLI argument** — `EmissionsTracker(telemetry_level=...)` or `codecarbon monitor --telemetry-level ...`
2. **Config + environment** — `telemetry_level` in `.codecarbon.config`, then `CODECARBON_TELEMETRY_LEVEL` when both are set
3. **Default:** `minimal` (Tier 1)

## Lifecycle

```text
EmissionsTracker.__init__  →  collect hardware/geo (no POST)
EmissionsTracker.stop()    →  minimal: private POST only  |  extensive: private POST + /emissions
```

If the run lasts less than one second, telemetry is not sent.

## Private telemetry (`minimal` and `extensive`) — per run

Both levels send the **same private payload** to `POST /telemetry` at each `stop()`. The `telemetry_level` field records which setting was used (`minimal` or `extensive`).

The payload includes:

- **Environment:** OS, Python, CPU/GPU/RAM, country/region, cloud provider/region, GPU driver/CUDA/cuDNN when available
- **Usage:** tracking mode, output methods, integration surface (library / CLI / offline), task tracking, CI/notebook/container/IDE hints, hardware diagnostics
- **ML stack:** framework presence flags **and** installed versions when detected
- **Run outcome:** duration, emissions, energy (total and per component), utilization averages

Private telemetry does **not** include project names, experiment ids, API keys, file paths, exact coordinates, executable/host hashes, or survey demographics (role, industry, etc.).

## `extensive` — additional public run summary

**Also** posts a **run emissions summary** to the shared CodeCarbon telemetry experiment via `ApiClient` (`/runs` then `/emissions`). Endpoint, API key, and experiment id come from `telemetry_api_url` / `telemetry_api_key` / `telemetry_experiment_id` (or `CODECARBON_TELEMETRY_*` env vars), falling back to the built-in defaults and your `api_endpoint` / `api_key` when set.

## Never collected

- Project name, experiment id, run id, API keys
- Source code, file paths, hostnames
- Exact GPS coordinates (`longitude` / `latitude`), `python_executable_hash`, `host_machine_hash`
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
codecarbon telemetry show
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

If you never set `telemetry_level`, CodeCarbon uses `minimal` (Tier 1) and logs a **one-time warning** per Python session. Set `telemetry_level` explicitly to silence it.

## Related

- [Configure CodeCarbon](configuration.md)
- [CLI reference](../reference/cli.md#codecarbon-telemetry)
- [Cloud API & dashboard](cloud-api.md)
