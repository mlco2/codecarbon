# Parameters

Parameters can be set via `EmissionsTracker()`, `OfflineEmissionsTracker()`, the
`@track_emissions` decorator, config files, or environment variables. See
[Configuration](../how-to/configuration.md) for priority order.

!!! note "PUE"
    PUE is a multiplication factor provided by the user. Old datacenters have PUE
    up to 2.2, new greener ones as low as 1.1.

!!! note "GPU selection"
    If you use `CUDA_VISIBLE_DEVICES` or `ROCR_VISIBLE_DEVICES` to set GPUs, CodeCarbon will automatically
    populate `gpu_ids`. Manual `gpu_ids` overrides this.

## Product telemetry

Optional library telemetry is controlled by **`telemetry_level`** on the tracker (same parameter on `OfflineEmissionsTracker` and `@track_emissions`):

| Value | Behavior |
|-------|----------|
| `disabled` | No product telemetry |
| `minimal` (default) | Tier 1 hardware/environment metadata once per process |
| `extensive` | Tier 1 + public emissions summary on `stop()` |

**Resolution order:** tracker argument → `.codecarbon.config` → `CODECARBON_TELEMETRY_LEVEL` → default `minimal`. The tracker argument overrides config and environment.

This is separate from `save_to_api` (your dashboard experiment). See [Product telemetry](../how-to/telemetry.md).

## EmissionsTracker / BaseEmissionsTracker

`EmissionsTracker` and `OfflineEmissionsTracker` inherit from `BaseEmissionsTracker`.
All parameters are documented below:

::: codecarbon.emissions_tracker.BaseEmissionsTracker
    options:
      members: 
        - __init__
      merge_init_into_class: true
      show_root_heading: true
      show_signature: false

## OfflineEmissionsTracker (additional parameters)

`OfflineEmissionsTracker` adds these parameters for offline mode:

::: codecarbon.emissions_tracker.OfflineEmissionsTracker
    options:
      members: 
        - __init__
      merge_init_into_class: true
      show_root_heading: true
      show_signature: false

## @track_emissions Decorator

The decorator accepts the same parameters as `EmissionsTracker`, plus `offline`
and `country_iso_code` for offline mode:

::: codecarbon.emissions_tracker.track_emissions
    options:
      show_root_heading: true
      show_signature: false
