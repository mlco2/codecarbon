# CLI Reference

CodeCarbon provides a command-line interface for tracking emissions without modifying code.

## Commands

### `codecarbon config`

Create or modify a `.codecarbon.config` configuration file interactively.

### `codecarbon login`

Authenticate with the CodeCarbon API and save credentials to your config file.

### `codecarbon monitor`

Monitor emissions from your machine continuously. Use `Ctrl+C` to stop.

**Options:**

| Option | Description |
|--------|-------------|
| `--no-api` | Disable sending data to the API (local-only measurement) |
| `--offline` | Run without internet access |
| `--country-iso-code CODE` | ISO 3166-1 alpha-3 country code (required in offline mode) |
| `--log-level LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) |
| `--` | Run a specific command and track its emissions |

### `codecarbon monitor -- <command>`

Track emissions for a specific command. The double hyphen `--` separates CodeCarbon options from the command to run.

### `codecarbon detect`

Detect and print hardware information (RAM, CPU, GPU).

!!! note "Work in progress"

    This reference page is a placeholder. See the [CLI tutorial](../tutorials/cli.md) for detailed usage examples.
