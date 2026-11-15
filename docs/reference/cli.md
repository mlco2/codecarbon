# CLI Reference

CodeCarbon provides a command-line interface for tracking emissions without modifying code.

## Global options

| Option | Description |
|--------|-------------|
| `--version`, `-v` | Show the installed CodeCarbon version and exit |

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
| `--project-name` | string | - | Project name for the current experiment |
| `--measure-power-secs` | int | 10 | Interval in seconds between two measures |
| `--api-call-interval` | int | 30 | Number of measures between API calls |
| `--api` / `--no-api` | flag | `--api` | Send data to the API, or do not (local-only measurement) |
| `--offline` / `--no-offline` | flag | `--no-offline` | Run without internet access |
| `--country-iso-code` | string | - | 3-letter country ISO code. Required in offline mode, unless it is set in the config file |
| `--region` | string | - | Region or province, for offline mode |
| `--log-level` | string | error | Log level: critical, error, warning, info, debug |

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

### `codecarbon get-token`

Get an API token for a project.

**Usage:**
```bash
codecarbon get-token PROJECT_ID
```

Requests a new API token for the project `PROJECT_ID` and prints it. Add it to the `api_key` field of your configuration file. You must be logged in first (see `codecarbon login`).

### `codecarbon test-api`

Check that your API access works.

**Usage:**
```bash
codecarbon test-api
```

Makes an authenticated request to the CodeCarbon API and prints the list of your organizations.
