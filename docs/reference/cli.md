# CLI Reference

CodeCarbon provides a command-line interface for tracking emissions without modifying code.

## Commands

### `codecarbon config`

Create or modify a `.codecarbon.config` configuration file interactively.

**Usage:**
```bash
codecarbon config
```

Prompts you to enter your configuration settings such as API credentials, project name, and tracking preferences. You can re-run this command to modify existing settings.

### `codecarbon login`

Authenticate with the CodeCarbon API and save credentials to your config file.

**Usage:**
```bash
codecarbon login
```

Opens a browser or provides a login link to authenticate with the CodeCarbon API. Saves your API token and creates a default experiment in `.codecarbon.config`.

### `codecarbon monitor`

Monitor emissions from your entire machine continuously.

**Usage:**
```bash
codecarbon monitor [OPTIONS]
```

Displays real-time emissions data for all processes on your machine. Press `Ctrl+C` to stop.

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-api` | flag | false | Do not send data to the API (local-only measurement) |
| `--offline` | flag | false | Run without internet access |
| `--country-iso-code` | string | - | ISO 3166-1 alpha-3 country code (required in offline mode) |
| `--log-level` | choice | ERROR | Log level: DEBUG, INFO, WARNING, ERROR |

**Examples:**
```bash
# Monitor with API (default)
codecarbon monitor

# Monitor locally without sending to API
codecarbon monitor --no-api

# Monitor offline
codecarbon monitor --offline --country-iso-code FRA

# Monitor with debug logging
codecarbon monitor --log-level DEBUG
```

### `codecarbon monitor -- <command>`

Track emissions for a specific command or process.

**Usage:**
```bash
codecarbon monitor -- <your_command>
```

Runs your command and tracks the emissions produced by that process only. The double hyphen `--` separates CodeCarbon options from the command to run.

**Examples:**
```bash
# Run a Python script with tracking
codecarbon monitor -- python train_model.py

# Run a shell script
codecarbon monitor -- bash benchmark.sh

# Run a command with arguments
codecarbon monitor -- node app.js --port 8080
```

**Options:**

Same options as `codecarbon monitor` apply (see above).

### `codecarbon wait -- <command>`

Wait for the greenest window in the carbon intensity forecast, then run a command under measurement.

**Usage:**
```bash
codecarbon wait [OPTIONS] -- <your_command>
```

CodeCarbon fetches an hourly carbon intensity forecast for your location from
[Electricity Maps](https://api.electricitymaps.com), picks the start time that minimises the
average intensity over the expected job length, sleeps until then, and finally hands the command
to `codecarbon monitor` — so measurement, CSV output and exit-code propagation are identical.

This is a sleep, not a scheduler: the process stays in the foreground and does not fork, daemonise
or persist across a reboot. For deferral that must survive a reboot, use cron, systemd or Airflow.
Pressing `Ctrl+C` during the wait does not abort — it starts the job immediately. The emissions
tracker only starts after the sleep, so a waiting process holds no lock.

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--duration` | string | 1h | Expected job length, e.g. `90m`, `2h`, `1h30m`, or a plain number of seconds |
| `--deadline` | string | 12h | Maximum delay before the job must start |
| `--threshold` | float | - | gCO2e/kWh at or below which the job starts immediately, without waiting |
| `--dry-run` | flag | false | Print the recommendation and exit without waiting or running |
| `--measure-power-secs` | int | 10 | Interval between two measures |
| `--log-level` | choice | error | Log level: critical, error, warning, info, debug |

**Examples:**
```bash
# Print the recommendation and exit
codecarbon wait --dry-run --deadline 24h --duration 90m

# Block until the greenest window, then run under measurement
codecarbon wait --deadline 12h --duration 2h -- python train.py

# Start straight away if the grid is already below 100 gCO2e/kWh
codecarbon wait --threshold 100 --deadline 6h -- bash benchmark.sh
```

The dry run prints the chosen window, for example:

```console
$ codecarbon wait --dry-run --deadline 24h --duration 90m
🌱 Best start: 2026-08-13 03:00 UTC  (112 gCO2e/kWh, now: 341)  -> saves ~67%
```

**Requirements:**

A forecast is only available with an `electricitymaps_api_token` (the `co2_signal_api_token` key
is also accepted) — see [Electricity Maps API Token](../how-to/configuration.md#electricity-maps-api-token).
The location is detected automatically from your IP address; there is no offline or
`--country-iso-code` option for this command.

**When no forecast is available:**

A forecast is an optimisation, never a requirement — the job is never blocked on a missing
credential. If no token is configured, or the API returns an error, a malformed payload or an
empty forecast, CodeCarbon prints `no forecast available, running now.` and starts the command
straight away. The same applies when no complete window fits before the deadline, or when the
forecast says now is already the greenest moment.

### `codecarbon detect`

Detect and print hardware information.

**Usage:**
```bash
codecarbon detect
```

Displays detected RAM, CPU, GPU, and other hardware information that CodeCarbon uses to estimate energy consumption. Useful for verifying that CodeCarbon can see all your hardware.
