# Product telemetry

CodeCarbon sends **anonymous product telemetry** to help improve the library: the hardware and software environment it runs on. It is **on by default (opt-out)**. This is separate from sending **your** emissions to the [dashboard](cloud-api.md) with `save_to_api=True`.

## Telemetry vs your dashboard data

| | Product telemetry | Your emissions (`save_to_api`) |
|--|-------------------|--------------------------------|
| Purpose | Improve CodeCarbon (aggregate usage) | Your projects and experiments |
| Config | `telemetry_level`, `codecarbon telemetry` | `codecarbon config`, `experiment_id` |
| Endpoint | `POST /telemetry`, no API key | Your account / experiment |

You can use one without the other.

## Levels

| `telemetry_level` | What is sent |
|-------------------|--------------|
| `disabled` | Nothing |
| `minimal` (default) | The fields listed below, once per process |

The level is resolved in this order:

1. **Tracker or CLI argument**: `EmissionsTracker(telemetry_level=...)` or `codecarbon monitor --telemetry-level ...`
2. **`CODECARBON_TELEMETRY_LEVEL`**: overrides the config file when both are set
3. **Config file**: `telemetry_level` in `.codecarbon.config`
4. **Default:** `minimal`

Telemetry is sent **once per process**, at the first `stop()` of a run that lasted at least one second; later `stop()` calls in the same process send nothing. The payload is built and sent on a background thread, so `stop()` never waits on it. At interpreter exit, a pending send gets at most one second before it is dropped.

## Every field sent

Empty or unknown values are left out rather than sent as zeros.

| Field | Content |
|-------|---------|
| `timestamp` | Hour of the send (UTC), truncated to the hour |
| `telemetry_level` | Always `minimal` |
| `os` | Platform string, for example `Linux-5.10.0-x86_64` |
| `country_name`, `country_iso_code`, `region` | Location as already detected by the tracker |
| `cloud_provider`, `cloud_region` | Cloud provider and region, when on a cloud |
| `cpu_count`, `cpu_physical_count`, `cpu_model`, `cpu_architecture` | CPU |
| `gpu_count`, `gpu_model`, `gpu_memory_total_gb`, `gpu_driver_version`, `cuda_version`, `cudnn_version` | GPU, when present |
| `ram_total_size_gb` | Total RAM |
| `python_version`, `python_implementation`, `python_env_type` | Python interpreter and environment type (`conda`, `venv` or `system`) |
| `codecarbon_version`, `codecarbon_install_method` | CodeCarbon version and how it was installed (`pip`, `uv`, `editable`) |

## Never collected

- Project name, experiment id, run id, API keys
- Emissions, energy, duration or any other run measurement
- Source code, file paths, hostnames
- Coordinates (latitude and longitude)
- Voluntary [user survey](https://docs.google.com/forms/d/e/1FAIpQLSeQ5Tu_rdrpDhBJvh5R1-_iB4Ld-kgh6iNMjgaMXa8AEVPxqA/viewform) answers

## Retention

Retention period: TBD by maintainers.

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

## Offline mode

`OfflineEmissionsTracker` and `codecarbon monitor --offline` never send telemetry, regardless of `telemetry_level` in config, environment or argument: offline mode is chosen for runs with no network access.

## Opt out

```ini
[codecarbon]
telemetry_level = disabled
```

Or set `CODECARBON_TELEMETRY_LEVEL=disabled`, or run `codecarbon telemetry set disabled` (writes to the global `~/.codecarbon.config`, creating it if missing; pass `--config` to target a specific file instead).

## First run without explicit configuration

Telemetry is on by default (`minimal`), and you are told about it once:

- **Interactive CLI** (`codecarbon config` or `codecarbon monitor` in a terminal): you are asked once which level you want. The answer is saved as `telemetry_level` in `~/.codecarbon.config`.
- **Everything else** (library use, CI, SLURM, pipes): nothing ever blocks on a prompt. CodeCarbon logs a notice **once per machine** saying what is sent and how to opt out, and remembers that it did in `~/.codecarbon/telemetry_notice_shown`.

Set `telemetry_level` explicitly to skip both.

## Related

- [Configure CodeCarbon](configuration.md)
- [CLI reference](../reference/cli.md#codecarbon-telemetry)
- [Cloud API & dashboard](cloud-api.md)
