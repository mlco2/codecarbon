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

### `codecarbon badge`

Generate a README badge from an existing `emissions.csv`.

**Usage:**
```bash
codecarbon badge [OPTIONS]
```

Reads the emissions file, writes `codecarbon-badge.json` (a
[shields.io endpoint](https://shields.io/badges/endpoint-badge) file) and prints a
markdown snippet to paste into your README. Everything happens locally: no network
call, no account, no data leaves your machine.

CodeCarbon writes one CSV row per flush, each holding the cumulative total of its
run, so the badge uses the last row of each `run_id`: `last` is the latest run,
`total` the sum over runs, `mean` the average per run.

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--file` | path | ./emissions.csv | Emissions file to read |
| `--project` | string | - | Only use rows of this project |
| `--select` | choice | last | Which run(s) to report: `last`, `mean` or `total` |
| `--metric` | choice | emissions | What to show: `emissions`, `energy` or `both` |
| `--output-dir` | path | . | Where to write the badge file |
| `--label` | string | carbon | Left-hand badge text |
| `--color` | string | grey | Badge colour |

**Examples:**
```bash
# Badge for the last run
codecarbon badge

# Average over every run of one project, showing energy too
codecarbon badge --project my-training --select mean --metric both

# Write into the docs assets folder
codecarbon badge --output-dir docs/assets
```

The badge is colour-neutral by default, and reports exactly what the CSV contains.
Keep in mind that CodeCarbon values are estimates: CPU power may come from a TDP
model and carbon intensity is often a country average, so a badge is a useful
order-of-magnitude signal rather than an audited figure. If you want a colour, pass
`--color` explicitly.

Regenerate the badge in CI after a benchmark job, publish `codecarbon-badge.json`
at a public URL and point shields.io at it:

```markdown
![carbon](https://img.shields.io/endpoint?url=https://example.org/codecarbon-badge.json)
```
