# Tracking with the CLI {#usage-command-line}

By the end of this tutorial, you'll be able to monitor any process's carbon emissions from the command line without writing any Python code.

CodeCarbon provides a command-line interface to track emissions without modifying your source code. In this tutorial, you'll set up the CLI, monitor your machine's emissions, and run commands with built-in emissions tracking.

## Setup

Create a minimal configuration file (just follow the prompts) :

``` console
codecarbon config
```

[![Init config](https://asciinema.org/a/667970.svg){.align-center}](https://asciinema.org/a/667970)

Then login from your terminal to authenticate CLI/API usage:

``` console
codecarbon login
```

You can use the same command to modify an existing config :

[![Modify config](https://asciinema.org/a/667971.svg){.align-center}](https://asciinema.org/a/667971)

With the configuration created, you're ready to start monitoring.

## Monitor Your Machine

If you want to track the emissions of a computer without having to
modify your code, you can use :

``` console
codecarbon monitor
```

You have to stop the monitoring manually with `Ctrl+C`.

If you only need local measurement and do not want to send data to the API,
use:

``` console
codecarbon monitor --no-api
```

You can also run CodeCarbon in offline mode without internet:

``` console
codecarbon monitor --offline --country-iso-code FRA
```

## Detect Your Hardware

Next, let's check what hardware CodeCarbon detected on your machine:

If you want to detect the hardware of your computer without starting any
measurement, you can use:

``` console
codecarbon detect
```

This will display your detected RAM, CPU, and GPU information, which CodeCarbon uses to estimate energy consumption.

## Track Any Command

The most powerful CLI feature is the ability to track any command or process automatically. This is especially useful for non-Python users or for monitoring existing shell scripts.

Use the `codecarbon monitor --` command to automatically track emissions from any process:

``` console
codecarbon monitor -- <your_command>
```

Do not surround `<your_command>` with quotes. The double hyphen `--`
indicates the end of CodeCarbon options and the beginning of the command
to run.

**Examples:**

``` console
# Run a shell script
codecarbon monitor -- ./benchmark.sh

# Run a command with arguments (use quotes for special characters)
codecarbon monitor -- bash -c 'echo "Processing..."; sleep 30; echo "Done!"'

# Run Python scripts
codecarbon monitor -- python train_model.py

# Run Node.js applications
codecarbon monitor -- node app.js

# Run tests with output redirection
codecarbon monitor -- npm run test > output.txt

# Display the CodeCarbon detailed logs
codecarbon monitor --log-level debug -- python --version
```

**Output:**

When the command completes, CodeCarbon displays a summary report and
saves the emissions data to a CSV file:

``` console
🌱 CodeCarbon: Starting emissions tracking...
   Command: bash -c echo "Processing..."; sleep 30; echo "Done!"

Processing...
Done!

============================================================
🌱 CodeCarbon Emissions Report
============================================================
   Command: bash -c echo "Processing..."; sleep 30; echo "Done!"
   Emissions: 0.0317 g CO2eq
   Saved to: /home/user/emissions.csv
   ⚠️  Note: Measured entire machine (includes all system processes)
============================================================
```

!!! note "Note"

    The `codecarbon monitor --` command tracks the specific process you run. For continuous machine-level tracking, use the plain `codecarbon monitor` command instead.

---

## What's Next?

You've now learned how to track emissions from the command line. Next steps:

- **Track in Python**: Use the [Python API tutorial](python-api.md) for fine-grained tracking within your code.
- **Send to Dashboard**: Learn how to [send data to the CodeCarbon dashboard](../how-to/cloud-api.md).
- **Configure Details**: See the [configuration guide](../how-to/configuration.md) for advanced options like proxy setup.

## See Also

- [CLI Reference](../reference/cli.md) for a complete list of commands and options
- [Use the Cloud API & Dashboard](../how-to/cloud-api.md) to send emissions to the online dashboard
- [Configure CodeCarbon](../how-to/configuration.md) for config files, environment variables, and proxy setup
