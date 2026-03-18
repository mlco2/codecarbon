# Tracking with the CLI {#usage-command-line}

CodeCarbon provides a command-line interface to track emissions without modifying your code.

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

## Monitor your machine

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

## Detect hardware

If you want to detect the hardware of your computer without starting any
measurement, you can use:

``` console
codecarbon detect
```

It will print the detected RAM, CPU and GPU information.

## Monitor with API

In the following example you will see how to use the CLI to monitor all
the emissions of you computer and sending everything to an API running
on "localhost:8008" (Or you can start a private local API with
"docker-compose up"). Using the public API with this is not supported
yet (coming soon!)

[![Monitor example](https://asciinema.org/a/667984.svg){.align-center}](https://asciinema.org/a/667984)

The command line could also works without internet by providing the
country code like this:

``` console
codecarbon monitor --offline --country-iso-code FRA
```

## Running Any Command with CodeCarbon

If you want to track emissions while running any command or program (not
just Python scripts), you can use the `codecarbon monitor --` command.
This allows non-Python users to measure machine emissions during the
execution of any command:

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

    The `codecarbon monitor --` command tracks process-level emissions (only
    the specific command), not the entire machine. For machine-level
    tracking, use the `codecarbon monitor` command.

    For more fine-grained tracking, implementing CodeCarbon in your code
    allows you to track the emissions of a specific block of code.

## See also

- [CLI Reference](../reference/cli.md) for a complete list of commands and options
- [Use the Cloud API & Dashboard](../how-to/cloud-api.md) to send emissions to the online dashboard
- [Configure CodeCarbon](../how-to/configuration.md) for config files, environment variables, and proxy setup
