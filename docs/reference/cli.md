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

Detect and print hardware information.

**Usage:**
```bash
codecarbon detect
```

Displays detected RAM, CPU, GPU, and other hardware information that CodeCarbon uses to estimate energy consumption. Useful for verifying that CodeCarbon can see all your hardware.

### `codecarbon doctor`

Report, for each power component, whether CodeCarbon measures it or estimates it.

**Usage:**
```bash
codecarbon doctor [OPTIONS]
```

CodeCarbon always produces a number, but on many machines part of it comes from a
model rather than from a hardware energy counter: the CPU falls back to a load
model when RAPL is not readable, RAM is always modelled, and a GPU that no driver
exposes contributes nothing. `doctor` runs the normal hardware detection and
prints the status of each component, why a better method was not used, and the
concrete fix.

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | flag | false | Print the report as JSON, for CI checks and bug reports |
| `--strict` | flag | false | Exit with code 1 if a component that could be measured is estimated |

**Example output:**
```text
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

- `MEASURED` — read from a hardware energy counter (RAPL, PowerMetrics, the
  Windows Energy Meter Interface, NVML or AMDSMI).
- `ESTIMATED` — derived from a model, typically CPU load over a TDP value.
- `UNAVAILABLE` — the component was not found and contributes nothing.

Use `--strict` in CI to fail a job when a machine silently falls back to
estimation, and paste `codecarbon doctor --json` into bug reports.

`--strict` only fails on components that *could* have been measured. RAM is
exempt: no platform exposes a DRAM energy counter to CodeCarbon, so RAM is
`ESTIMATED` on every machine and failing on it would make `--strict` a gate
nothing can pass. An absent GPU is exempt for the same reason, being
`UNAVAILABLE` rather than a failure.
