# Product telemetry

CodeCarbon can send **optional product telemetry** to help improve the library: which hardware and environments people use, and (if you opt in) anonymous run emissions on a public leaderboard.

This is **separate from** your own dashboard setup (`codecarbon config`, `codecarbon login`, `save_to_api`). Those commands configure **your** project and experiments. Product telemetry uses the shared settings below.

## Telemetry tiers

| Tier | `telemetry_level` | When | What is sent |
|------|-------------------|------|----------------|
| **0** | `disabled` | — | Nothing |
| **1** | `minimal` (default) | Once per Python process, when the tracker starts | Minimal hardware / environment metadata (see below) |
| **2** | `extensive` | Tier 1 on start **and** Tier 2 on `stop()` | Tier 1 plus one public emissions row for the run |

If you never set `telemetry_level`, CodeCarbon uses **`minimal`** and logs a **one-time warning** per Python session telling you that Tier 1 will be sent.

## Tier 1: what we collect today

Tier 1 sends a single `POST` to `{telemetry_api_url}/telemetry` the first time an `EmissionsTracker` or `OfflineEmissionsTracker` is created in a process (not on every run).

Only the fields below are included. Any value that is unknown is **omitted** from the payload (not sent as `null`).

| Field | Description |
|-------|-------------|
| `timestamp` | UTC time when the tracker was initialized |
| `telemetry_level` | Always `minimal` for this tier |
| `os` | Operating system string (e.g. platform description) |
| `country_iso_code` | ISO country code when known (e.g. offline mode or geo lookup) |
| `region` | Region or cloud region when known |
| `cloud_provider` | Cloud provider name when known |
| `cloud_region` | Same as `region` when cloud metadata is available |
| `longitude` | Approximate longitude when known (degrees) |
| `latitude` | Approximate latitude when known (degrees) |
| `cpu_count` | Logical CPU count |
| `cpu_physical_count` | Physical CPU count |
| `cpu_model` | CPU model name |
| `gpu_count` | Number of GPUs detected |
| `gpu_model` | GPU model name(s) |
| `ram_total_size_gb` | Total RAM in GB |
| `python_version` | Python version string |
| `codecarbon_version` | Installed CodeCarbon version |

### Tier 1: what we do **not** collect yet

The API schema supports more “minimal” fields (framework versions, install method, executable hash, etc.). **The client does not send them today.** In particular, Tier 1 does **not** include:

- Run duration, energy, or CO₂ emissions
- CPU/GPU utilization or power samples
- Project, experiment, or user identifiers from your dashboard config
- Python executable hash, virtualenv type, or ML framework versions
- IDE, CI, or notebook environment metadata

If we add fields later, this page will be updated; the payload will stay limited to the minimal tier rules on the server.

## Tier 2: extensive (public leaderboard)

When `telemetry_level = extensive`, CodeCarbon still sends Tier 1 once per process, and on **`stop()`** posts **one** emissions summary to the shared telemetry experiment via the same API used for leaderboard data (`add_emission`). That is independent of `save_to_api` (your private dashboard uploads).

Use this only if you are comfortable contributing anonymous run-level emissions to the public experiment.

## Configure telemetry

### Config file

Add to `~/.codecarbon.config` and/or `./.codecarbon.config`:

```ini
[codecarbon]
telemetry_level = minimal
```

Allowed values: `disabled`, `minimal`, `extensive`.

Optional API overrides (defaults point at the public telemetry project):

```ini
telemetry_api_url = https://api.codecarbon.io
telemetry_api_key = cpt_...
telemetry_experiment_id = aa69b440-014a-4562-ac06-ba7eecb023f9
```

Environment variables for URL, key, and experiment id: `CODECARBON_TELEMETRY_API_URL`, `CODECARBON_TELEMETRY_API_KEY`, `CODECARBON_TELEMETRY_EXPERIMENT_ID`.

**Tier resolution:** `telemetry_level` in the config file, or the tracker / CLI override below. Environment variables such as `CODECARBON_TELEMETRY_LEVEL` or legacy `CODECARBON_TELEMETRY` can mark your choice as “explicit” (so the default warning is skipped) but **do not** change the tier unless the same value is also in the config file or passed to the tracker.

### CLI

```bash
# Interactive wizard
codecarbon telemetry

# Set tier in a config file
codecarbon telemetry set disabled
codecarbon telemetry show

# One-run override (does not write the config file)
codecarbon monitor --telemetry-level minimal -- python train.py
```

See the [CLI reference](../reference/cli.md#codecarbon-telemetry) for details.

### Python

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(telemetry_level="disabled")
```

`OfflineEmissionsTracker`, `@track_emissions`, and `codecarbon monitor` accept the same `telemetry_level` argument.

### Disable telemetry in tests

```ini
[codecarbon]
telemetry_level = disabled
```

## Privacy notes

- Tier 1 is **best-effort**: failures are logged and do not block tracking.
- Coordinates are only sent when the tracker already resolved them; they are not precise location tracking by themselves.
- Choose `disabled` if you do not want any product telemetry.
- Choose `extensive` only if you accept publishing one emissions row per process to the public telemetry experiment on stop.

## Related

- [Configure CodeCarbon](configuration.md) — general config file and environment variables
- [Use the Cloud API & Dashboard](cloud-api.md) — your own projects and experiments
