# Configure CodeCarbon

## Configuration priority

CodeCarbon is structured so that you can configure it in a hierarchical manner:

-   *global* parameters in your home folder `~/.codecarbon.config`
-   *local* parameters (with respect to the current working
    directory) in `./.codecarbon.config`
-   *environment variables* parameters starting with `CODECARBON_`
-   *script* parameters in the tracker's initialization as
    `EmissionsTracker(param=value)`

!!! warning "Configuration files"

    Configuration files **must** be named `.codecarbon.config` and start
    with a section header `[codecarbon]` as the first line in the file.

    For instance:

    -   `~/.codecarbon.config`

        ``` bash
        [codecarbon]
        measure_power_secs=10
        output_methods=csv
        emissions_endpoint=localhost:7777
        ```

    -   `./.codecarbon.config` will override `~/.codecarbon.config` if the
        same parameter is set in both files:

        ``` bash
        [codecarbon]
        output_methods = csv,logger
        output_dir = /Users/victor/emissions
        electricitymaps_api_token=script-overwrite
        experiment_id = 235b1da5-aaaa-aaaa-aaaa-893681599d2c
        log_level = DEBUG
        tracking_mode = process
        ```

    -   environment variables will override `./.codecarbon.config` if the
        same parameter is set in both files:

        ``` bash
        export CODECARBON_GPU_IDS="0, 1"
        export CODECARBON_LOG_LEVEL="WARNING"
        ```

    -   script parameters will override environment variables if the same
        parameter is set in both:

        ``` python
        EmissionsTracker(
           api_call_interval=4,
           electricitymaps_api_token="some-token")
        ```

Yields attributes:

``` python
{
    "measure_power_secs": 10,  # from ~/.codecarbon.config
    "output_methods": "csv,logger",   # from ./.codecarbon.config (override ~/.codecarbon.config)
    "api_call_interval": 4, # from script
    "experiment_id": "235b1da5-aaaa-aaaa-aaaa-893681599d2c", # from ./.codecarbon.config
    "log_level": "WARNING", # from environment variable (override ./.codecarbon.config)
    "tracking_mode": "process", # from ./.codecarbon.config
    "emissions_endpoint": "localhost:7777", # from ~/.codecarbon.config
    "output_dir": "/Users/victor/emissions", # from ./.codecarbon.config
    "electricitymaps_api_token": "some-token", # from script (override ./.codecarbon.config)
    "gpu_ids": [0, 1], # from environment variable
}
```

!!! note "Where does a value come from?"

    CodeCarbon logs one line listing every configuration key read from the files
    and the environment, with the layer it came from, so you can trace a
    surprising value back to its source:

    ```
    [codecarbon INFO @ 09:30:00] Codecarbon configuration: experiment_id from CODECARBON_EXPERIMENT_ID, measure_power_secs from /home/victor/.codecarbon.config
    ```

    Only the key names and their source are logged, never the values, as this
    configuration holds secrets such as `api_key`.

!!! note "Note"

    If you're wondering about the configuration files' syntax, be aware
    that under the hood `codecarbon` uses
    [`ConfigParser`](https://docs.python.org/3/library/configparser.html#module-configparser)
    which relies on the [INI
    syntax](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure).

## Configuration keys

These are all the keys that the tracker reads from the configuration files, the environment and the constructor. Each key can also be set as the environment variable `CODECARBON_<KEY>`, where `<KEY>` is the key in upper case. For example, `CODECARBON_LOG_LEVEL` sets `log_level`.

| Key | Default |
|-----|---------|
| `allow_multiple_runs` | `True` |
| `electricitymaps_api_token` | none |
| `output_methods` | none |
| `save_to_api` | `False` |
| `save_to_file` | `True` |
| `save_to_logger` | `False` |
| `save_to_prometheus` | `False` |
| `save_to_logfire` | `False` |
| `force_carbon_intensity_g_co2e_kwh` | none |
| `api_call_interval` | `8` |
| `api_endpoint` | `https://api.codecarbon.io` |
| `api_key` | `api_key` |
| `emissions_endpoint` | none |
| `experiment_name` | `base` |
| `gpu_ids` | none |
| `log_level` | `info` |
| `measure_power_secs` | `15` |
| `output_dir` | `.` |
| `output_file` | `emissions.csv` |
| `project_name` | `codecarbon` |
| `logging_logger` | none (constructor only: a Python object) |
| `prometheus_url` | `localhost:9091` |
| `output_handlers` | `[]` (constructor only: Python objects) |
| `tracking_mode` | `machine` |
| `on_csv_write` | `append` |
| `metadata` | none |
| `logger_preamble` | empty string |
| `force_cpu_power` | none |
| `force_ram_power` | none |
| `pue` | `1.0` |
| `wue` | `0` |
| `force_mode_cpu_load` | `False` |
| `rapl_include_dram` | `False` |
| `rapl_prefer_psys` | `False` |
| `experiment_id` | `5b0fa12a-3dd7-45bb-9766-cc326314d9f1` |
| `cloud_provider` | none |
| `cloud_region` | none |
| `country_2letter_iso_code` | none |
| `country_iso_code` | none |
| `region` | none |

A default of "none" means the key is unset unless you provide a value. `save_to_*` keys are deprecated and are ignored when `output_methods` is set. The `cloud_*`, `country_*` and `region` keys are read by `OfflineEmissionsTracker`.

## Electricity Maps API Token

By default, CodeCarbon estimates carbon intensity using annual country-level
averages from Our World in Data. Providing an `electricitymaps_api_token`
upgrades this to **real-time carbon intensity** data from the
[Electricity Maps API](https://api.electricitymaps.com), giving more accurate
emissions figures — especially useful if your grid's energy mix varies
throughout the day.

**Without a token:** CodeCarbon uses a static annual average for your country.

**With a token:** CodeCarbon queries the Electricity Maps API for the current
carbon intensity of your grid. The query runs at the end of each tracking run,
and also periodically during long runs (every
`api_call_interval × measure_power_secs` seconds; default: every ~2 minutes).

!!! warning "Carbon intensity is cached for 60 seconds"

    A fetched carbon intensity is reused for 60 seconds before the API is
    queried again, so measurements taken within that window share the same
    intensity value. With default settings the periodic query runs every ~2
    minutes, so the cache mainly deduplicates closely spaced lookups (for
    example the final query in `stop()`, or several trackers in one process).
    After a failure (invalid token, network down), requests are skipped for a
    cooldown that starts at 30 seconds and doubles on each consecutive failure,
    up to 1 hour, per location and token; it resets after a successful request.
    Meanwhile CodeCarbon falls back to its own country data.

Direct access to the Electricity Maps API requires a paid plan or a
[14-day free trial](https://help.electricitymaps.com/en/articles/13335550-how-can-i-access-the-electricity-maps-api-and-are-there-any-restrictions).
Electricity Maps also offers a free
[Home Assistant license](https://help.electricitymaps.com/en/articles/13160873-how-to-get-an-electricity-maps-api-key-for-home-assistant),
but that key is restricted to a single zone and to the Home Assistant
integration; it will not work with CodeCarbon's direct API calls.

If you have a paid plan or trial token, set it in your config file:

``` ini
[codecarbon]
electricitymaps_api_token = your-token-here
```

Or in code:

``` python
EmissionsTracker(electricitymaps_api_token="your-token-here")
```

!!! note "Deprecated parameter"

    The old parameter name `co2_signal_api_token` still works for backward
    compatibility but is deprecated and will be removed in a future version.
    Use `electricitymaps_api_token` instead. See the
    [deprecations list](https://docs.codecarbon.io/latest/reference/deprecations/).

## National Grid ESO API (Great Britain)

For runs detected as being in Great Britain, CodeCarbon can optionally use
live carbon intensity data from the
[National Grid ESO Carbon Intensity API](https://carbonintensity.org.uk/)
instead of the static country-average data, by setting
`use_national_grid_eso_api=True`. This is **opt-in and off by default**,
the same way the Electricity Maps integration above is off until you provide
a token — it is not used automatically.

``` python
EmissionsTracker(use_national_grid_eso_api=True)
```

Or in your config file:

``` ini
[codecarbon]
use_national_grid_eso_api = true
```

The value is fetched with a 4-second timeout and cached for 5 minutes, shared
by all trackers in the same Python process. If a request fails, CodeCarbon
uses its static data and waits 30 seconds before retrying, doubling the wait
on each consecutive failure up to one hour.

**Attribution and terms of use:** data is published by National Grid ESO
under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
See [carbonintensity.org.uk](https://carbonintensity.org.uk/) for full terms.

**Scope:** the API reports a single **Great-Britain-wide (national)** carbon
intensity figure. It does not provide regional or sub-national data, so this
is not a substitute for CodeCarbon's USA/Canada/Nordic regional emissions
support. It covers the GB grid (England, Scotland, Wales) only: runs located
in Northern Ireland, which is on the all-island Irish grid, keep CodeCarbon's
static data.

If `electricitymaps_api_token` is also set, Electricity Maps takes priority
and this source is only used as a fallback if that call fails.

## Tracking Mode

The `tracking_mode` parameter controls how CodeCarbon measures power consumption. It accepts two values:

- **`"machine"`** (default): Measures power for the entire machine — total RAM in use and total CPU load across all processes.
- **`"process"`**: Isolates measurements to the tracked process — only the process's RAM usage and its share of CPU time are used to estimate power.

This setting affects **RAM and CPU** measurements. GPU power is always measured at the device level regardless of tracking mode.

Set it in your config file:

``` ini
[codecarbon]
tracking_mode = process
```

Or in code:

``` python
EmissionsTracker(tracking_mode="process")
```

!!! note "Note"

    `"process"` mode gives a lower-bound estimate of your code's footprint.
    `"machine"` mode is more conservative and accounts for all activity on the system.

## Including DRAM in the CPU Measurement

When CodeCarbon reads the CPU energy counters, the hardware also exposes a
`DRAM` domain measuring the memory controller. It is **excluded by default**, so
that memory power is reported by the RAM tracker only and is not counted twice.

Set `rapl_include_dram` to add it to the CPU measurement:

``` ini
[codecarbon]
rapl_include_dram = true
```

Or in code:

``` python
EmissionsTracker(rapl_include_dram=True)
```

Despite its name, this option applies to every counter-based CPU interface:

- **Linux**: the `dram` domains of the [RAPL](../explanation/rapl.md) powercap
  interface.
- **Windows 11**: the `DRAM` channels of the Energy Meter Interface, which
  exposes the very same RAPL counters.

It has no effect when CodeCarbon falls back to TDP/CPU-load estimation, since
that mode models the CPU package only.

## Access internet through proxy server

If you need a proxy to access internet, which is needed to call a Web
API, like [Codecarbon API](https://api.codecarbon.io/docs), you have to
set environment variable `HTTPS_PROXY`, or *HTTP_PROXY* if calling an
`http://` endpoint.

You could do it in your shell:

``` shell
export HTTPS_PROXY="http://0.0.0.0:0000"
```

Or in your Python code:

``` python
import os

os.environ["HTTPS_PROXY"] = "http://0.0.0.0:0000"
```

For more information, please read the [requests library proxy
documentation](https://requests.readthedocs.io/en/latest/user/advanced/#proxies)
