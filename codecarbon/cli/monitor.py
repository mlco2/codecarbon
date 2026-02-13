"""CodeCarbon CLI - Monitor Command"""

import os
import subprocess
import sys

import typer
from rich import print
from typing_extensions import Annotated

from codecarbon.emissions_tracker import EmissionsTracker


def run_and_monitor(
    ctx: typer.Context,
    log_level: Annotated[
        str, typer.Option(help="Log level (critical, error, warning, info, debug)")
    ] = "error",
    **tracker_args,
):
    """
    Run a command and track its carbon emissions.

    This command wraps any executable and measures the process's total power
    consumption during its execution. When the command completes, a summary
    report is displayed and emissions data is saved to a CSV file.

    Note: This tracks process-level emissions (only the specific command), not the
    entire machine. For machine-level tracking, use the `monitor` command.

    Examples:

        Do not use quotes around the command. Use -- to separate CodeCarbon args.

        # Run any shell command:
        codecarbon monitor -- ./benchmark.sh

        # Commands with arguments (use single quotes for special chars):
        codecarbon monitor -- python -c 'print("Hello World!")'

        # Pipe the command output:
        codecarbon monitor -- npm run test > output.txt

        # Display the CodeCarbon detailed logs:
        codecarbon monitor --log-level debug -- python --version

    The emissions data is appended to emissions.csv (default) in the current
    directory. The file path is shown in the final report.
    """
    # Suppress all CodeCarbon logs during execution
    from codecarbon.external.logger import set_logger_level

    set_logger_level(log_level)

    # Get the command from remaining args
    command = ctx.args

    if not command:
        print(
            "ERROR: No command provided. Use: codecarbon monitor -- <command>",
            file=sys.stderr,
        )
        raise typer.Exit(1)

    # Initialize tracker with specified logging level and shared args
    tracker = EmissionsTracker(
        log_level=log_level,
        save_to_logger=False,
        tracking_mode="process",
        **tracker_args,
    )

    print("🌱 CodeCarbon: Starting emissions tracking...")
    print(f"   Command: {' '.join(command)}")
    print()

    tracker.start()

    process = None
    try:
        # Run the command, streaming output to console
        process = subprocess.Popen(
            command,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
        )

        # Wait for completion
        exit_code = process.wait()

    except FileNotFoundError:
        print(f"❌ Error: Command not found: {command[0]}", file=sys.stderr)
        exit_code = 127
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user", file=sys.stderr)
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        exit_code = 130
    except Exception as e:
        print(f"❌ Error running command: {e}", file=sys.stderr)
        exit_code = 1
    finally:
        emissions = tracker.stop()
        print()
        print("=" * 60)
        print("🌱 CodeCarbon Emissions Report")
        print("=" * 60)
        print(f"   Command: {' '.join(command)}")
        if emissions is not None:
            print(f"   Emissions: {emissions * 1000:.4f} g CO2eq")
        else:
            print("   Emissions: N/A")

        # Show where the data was saved
        if hasattr(tracker, "_conf") and "output_file" in tracker._conf:
            output_path = tracker._conf["output_file"]
            # Make it absolute if it's relative
            if not os.path.isabs(output_path):
                output_path = os.path.abspath(output_path)
            print(f"   Saved to: {output_path}")

        print("   ⚠️  Note: Tracked the command process and its children")
        print("=" * 60)

    raise typer.Exit(exit_code)
