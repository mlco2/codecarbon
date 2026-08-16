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

### `codecarbon detect`

Detect and print hardware information, with a measurement quality report.

**Usage:**
```bash
codecarbon detect [OPTIONS]
```

Displays detected RAM, CPU, GPU, and other hardware information that CodeCarbon
uses to estimate energy consumption. Useful for verifying that CodeCarbon can
see all your hardware.

Runs the normal hardware detection and reports, per component, whether it is
measured or estimated, and how to fix it.

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | flag | false | Print the hardware information and the report as JSON, for bug reports |

**Example output:**
```text
Detected Hardware and System Information:
- Available RAM: 31.084 GB
- CPU count: 16 thread(s) in 8 physical CPU(s)
- CPU model: 12th Gen Intel(R) Core(TM) i7-1260P
- GPU count: 1
- GPU model: 1 x NVIDIA A100-SXM4-40GB

CodeCarbon 3.3.0 - measurement quality report

RAM  31.1 GB
    ESTIMATED - RAM power estimation model
    Why: no platform exposes a DRAM energy counter to CodeCarbon
    Fix: none; see https://docs.codecarbon.io/explanation/methodology/#ram

CPU  12th Gen Intel(R) Core(TM) i7-1260P
    ESTIMATED - CPU load model over a 28 W TDP
    Why: /sys/class/powercap/intel-rapl exists but its energy counter is not
         readable by this user (permission denied)
    Fix: sudo chmod -R a+r /sys/class/powercap/intel-rapl

GPU  1 x NVIDIA A100-SXM4-40GB
    MEASURED - NVML/AMDSMI

1 of 3 power components are measured directly.
```

Statuses are:

- `MEASURED`: read from a hardware energy counter (RAPL, PowerMetrics, the
  Windows Energy Meter Interface, NVML or AMDSMI).
- `ESTIMATED`: derived from a model, typically CPU load over a TDP value.
- `UNAVAILABLE`: the component exists but its power cannot be read, so it
  contributes nothing. Hardware you do not have (no GPU, for instance) is not
  listed and is not counted in the summary.

Paste `codecarbon detect --json` into bug reports.
