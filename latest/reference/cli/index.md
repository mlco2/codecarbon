# CLI Reference

CodeCarbon provides a command-line interface for tracking emissions without modifying code.

## Global options

| Option | Description |
| --- | --- |
| `--version`, `-v` | Show the installed CodeCarbon version and exit |

## Commands

### `codecarbon config`

Create or modify a `.codecarbon.config` configuration file interactively.

**Usage:**

```
codecarbon config
```

Prompts you to enter your configuration settings such as API credentials, project name, and tracking preferences. You can re-run this command to modify existing settings.

### `codecarbon login`

Authenticate with the CodeCarbon API and save credentials to your config file.

**Usage:**

```
codecarbon login
```

Opens a browser or provides a login link to authenticate with the CodeCarbon API. Saves your API token and creates a default experiment in `.codecarbon.config`.

### `codecarbon monitor`

Monitor emissions from your entire machine continuously.

**Usage:**

```
codecarbon monitor [OPTIONS]
```

Displays real-time emissions data for all processes on your machine. Press `Ctrl+C` to stop.

**Options:**

Each option overrides the matching key of `.codecarbon.config` or `CODECARBON_*` variable (see [Configuration](<https://docs.codecarbon.io/latest/how-to/configuration/index.md>)). An option left out keeps the configured value. Each flag also has a negative form, such as `--no-rapl-include-dram`.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--project-name` | string | \- | Project name for the current experiment |
| `--measure-power-secs` | int | 10 | Interval in seconds between two measures |
| `--api-call-interval` | int | 30 | Number of measures between API calls |
| `--api` / `--no-api` | flag | `--api` | Add or remove the API from the output methods |
| `--offline` / `--no-offline` | flag | `--no-offline` | Run without internet access |
| `--country-iso-code` | string | \- | 3-letter country ISO code. Required in offline mode, unless it is set in the config file |
| `--region` | string | \- | Region or province, for offline mode |
| `--log-level` | string | error | Log level: critical, error, warning, info, debug |
| `--experiment-id` | string | \- | Experiment ID, satisfies the online-mode check |
| `--experiment-name` | string | \- | Experiment name |
| `--api-endpoint` | string | \- | CodeCarbon API endpoint |
| `--api-key` | string | \- | CodeCarbon API key |
| `--output-methods` | string | \- | Comma-separated output methods: `csv`, `api`, `logger`, `prometheus`, `logfire`, ... |
| `--output-dir` | string | \- | Directory for output files |
| `--output-file` | string | \- | Output CSV file name |
| `--on-csv-write` | string | \- | `append` or `update` |
| `--live-output-file` | string | \- | CSV file receiving every interval measurement |
| `--metadata` | string | \- | JSON file of metadata added to the outputs |
| `--prometheus-url` | string | \- | Prometheus push gateway URL |
| `--emissions-endpoint` | string | \- | HTTP endpoint receiving the emissions |
| `--logger-preamble` | string | \- | Text prefixed to the tracker log messages |
| `--gpu-ids` | string | \- | Comma-separated GPU IDs to track, such as `0,2` |
| `--tracking-mode` | string | \- | `machine` or `process` (`process` when wrapping a command) |
| `--force-cpu-power` | float | \- | CPU power in watts, replaces the estimate |
| `--force-ram-power` | float | \- | RAM power in watts, replaces the estimate |
| `--force-mode-cpu-load` | flag | \- | Estimate CPU power from its load |
| `--force-mode-constant` | flag | \- | Estimate CPU power as a constant fraction of its TDP, takes precedence over `--force-mode-cpu-load` |
| `--pue` | float | \- | Power Usage Effectiveness of the data center |
| `--wue` | float | \- | Water Usage Effectiveness, in L/kWh |
| `--force-carbon-intensity-g-co2e-kwh` | float | \- | Carbon intensity of the electricity, in gCO2e/kWh |
| `--electricitymaps-api-token` | string | \- | Electricity Maps API token |
| `--use-national-grid-eso-api` | flag | \- | In Great Britain, use the live National Grid ESO carbon intensity |
| `--rapl-include-dram` | flag | \- | Include DRAM in the RAPL measures |
| `--rapl-prefer-psys` | flag | \- | Prefer the RAPL platform (psys) domain |
| `--allow-multiple-runs` | flag | \- | Allow several CodeCarbon instances at the same time |
| `--save-to-file`, `--save-to-logger`, `--save-to-prometheus`, `--save-to-logfire` | flag | \- | Deprecated: use `--output-methods` |
| `--co2-signal-api-token` | string | \- | Deprecated: use `--electricitymaps-api-token` |

In online mode, `--output-methods` replaces the configured output methods, and `--api` / `--no-api` then adds or removes the API.

> [!WARNING]
>
> **Secrets on the command line**
>
> Other users of the machine can read command-line arguments, and your shell saves them in its history. Prefer the `CODECARBON_API_KEY` and `CODECARBON_ELECTRICITYMAPS_API_TOKEN` environment variables, or the configuration file, to `--api-key` and `--electricitymaps-api-token`.

**Examples:**

```
# Monitor with API (default)
codecarbon monitor

# Monitor locally without sending to API
codecarbon monitor --no-api

# Monitor offline
codecarbon monitor --offline --country-iso-code FRA

# Monitor with debug logging
codecarbon monitor --log-level DEBUG

# Monitor a server in a data center, writing to a CSV file and the logger
codecarbon monitor --no-api --pue 1.4 --output-methods csv,logger
```

### `codecarbon monitor -- <command>`

Track emissions for a specific command or process.

**Usage:**

```
codecarbon monitor -- <your_command>
```

Runs your command and tracks the emissions produced by that process only. The double hyphen `--` separates CodeCarbon options from the command to run.

**Examples:**

```
# Run a Python script with tracking
codecarbon monitor -- python train_model.py

# Run a shell script
codecarbon monitor -- bash benchmark.sh

# Run a command with arguments
codecarbon monitor -- node app.js --port 8080
```

**Options:**

Same options as `codecarbon monitor` apply (see above).

### `codecarbon detect`

Detect and print hardware information.

**Usage:**

```
codecarbon detect
```

Displays detected RAM, CPU, GPU, and other hardware information that CodeCarbon uses to estimate energy consumption. Useful for verifying that CodeCarbon can see all your hardware.

### `codecarbon get-token`

Get an API token for a project.

**Usage:**

```
codecarbon get-token PROJECT_ID
```

Requests a new API token for the project `PROJECT_ID` and prints it. Add it to the `api_key` field of your configuration file. You must be logged in first (see `codecarbon login`).

### `codecarbon test-api`

Check that your API access works.

**Usage:**

```
codecarbon test-api
```

Makes an authenticated request to the CodeCarbon API and prints the list of your organizations.
