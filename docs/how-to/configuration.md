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
        save_to_file=local-overwrite
        emissions_endpoint=localhost:7777
        ```

    -   `./.codecarbon.config` will override `~/.codecarbon.config` if the
        same parameter is set in both files:

        ``` bash
        [codecarbon]
        save_to_file = true
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
           save_to_api=True,
           electricitymaps_api_token="some-token")
        ```

Yields attributes:

``` python
{
    "measure_power_secs": 10,  # from ~/.codecarbon.config
    "save_to_file": True,   # from ./.codecarbon.config (override ~/.codecarbon.config)
    "api_call_interval": 4, # from script
    "save_to_api": True,   # from script
    "experiment_id": "235b1da5-aaaa-aaaa-aaaa-893681599d2c", # from ./.codecarbon.config
    "log_level": "WARNING", # from environment variable (override ./.codecarbon.config)
    "tracking_mode": "process", # from ./.codecarbon.config
    "emissions_endpoint": "localhost:7777", # from ~/.codecarbon.config
    "output_dir": "/Users/victor/emissions", # from ./.codecarbon.config
    "electricitymaps_api_token": "some-token", # from script (override ./.codecarbon.config)
    "gpu_ids": [0, 1], # from environment variable
}
```

!!! note "Note"

    If you're wondering about the configuration files' syntax, be aware
    that under the hood `codecarbon` uses
    [`ConfigParser`](https://docs.python.org/3/library/configparser.html#module-configparser)
    which relies on the [INI
    syntax](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure).

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

The Electricity Maps API offers a free tier. You can sign up and get a token at
[electricitymaps.com](https://app.electricitymaps.com/sign-up).

Set it in your config file:

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
    Use `electricitymaps_api_token` instead.

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
