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

### `codecarbon ci-report`

Summarise an `emissions.csv` for a CI pipeline, optionally against a baseline run.

**Usage:**
```bash
codecarbon ci-report [OPTIONS]
```

Reads the rows of the most recent run in the CSV (CodeCarbon appends one row per flush, all sharing the same `run_id`), sums them, and prints markdown or JSON. Nothing in the command is specific to a CI provider, so it works the same on GitHub Actions, GitLab CI, Jenkins or Buildkite.

**Options:**

| Option | Default | Description |
|---|---|---|
| `--csv PATH` | `emissions.csv` | Emissions CSV to summarise. |
| `--baseline PATH` | none | Emissions CSV to compare against, typically the target branch. A missing file is ignored and the comparison is simply omitted. |
| `--format [markdown\|json]` | `markdown` | Output format. |
| `--label TEXT` | project name | Label for the measured workload, shown in the report header. |
| `--threshold-kg FLOAT` | none | Exit with code 1 when total emissions exceed this many kgCO2eq. |

**Examples:**
```bash
# Measure a test suite, then report on it
codecarbon monitor -- pytest -q
codecarbon ci-report --label "pytest -q"

# Compare with a baseline downloaded from the target branch
codecarbon ci-report --baseline base/emissions.csv --label "pytest -q"

# Fail the pipeline above a budget
codecarbon ci-report --threshold-kg 0.05

# Machine-readable output for further processing
codecarbon ci-report --format json
```

Writing the markdown to a GitHub Actions job summary needs no token and no extra permissions:

```yaml
- run: codecarbon monitor -- pytest -q
- run: codecarbon ci-report --label "pytest -q" >> "$GITHUB_STEP_SUMMARY"
```

!!! warning "Accuracy on hosted CI runners"
    Hosted runners are virtualised, so RAPL is unavailable and CPU energy falls back to an estimate based on the CPU model TDP. Numbers are meaningful when comparing runs on identical runner types, not as absolute figures. For accurate measurements use a self-hosted runner with [RAPL enabled](../how-to/enable-rapl.md).
