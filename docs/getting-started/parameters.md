# Parameters

Parameters can be set via `EmissionsTracker()`, `OfflineEmissionsTracker()`, the
`@track_emissions` decorator, config files, or environment variables. See
[Configuration](usage.md#configuration) for priority order.

!!! note "PUE"
    PUE is a multiplication factor provided by the user. Old datacenters have PUE
    up to 2.2, new greener ones as low as 1.1.

!!! note "GPU selection"
    If you use `CUDA_VISIBLE_DEVICES` to set GPUs, CodeCarbon will automatically
    populate `gpu_ids`. Manual `gpu_ids` overrides this.

## EmissionsTracker / BaseEmissionsTracker

`EmissionsTracker` and `OfflineEmissionsTracker` inherit from `BaseEmissionsTracker`.
All parameters are documented below:

::: codecarbon.emissions_tracker.BaseEmissionsTracker
    options:
      members: __init__
      merge_init_into_class: true
      show_root_heading: true
      show_signature: false

## OfflineEmissionsTracker (additional parameters)

`OfflineEmissionsTracker` adds these parameters for offline mode:

::: codecarbon.emissions_tracker.OfflineEmissionsTracker
    options:
      members: __init__
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
