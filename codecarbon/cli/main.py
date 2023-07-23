import shlex
import sys

import click

from codecarbon.cli.cli_utils import (
    get_api_endpoint,
    get_existing_local_exp_id,
    write_local_exp_id,
)
from codecarbon.cli.monitor import monitor_infinite_loop, monitor_subprocess
from codecarbon.core.api_client import ApiClient, get_datetime_with_timezone
from codecarbon.core.schemas import ExperimentCreate

DEFAULT_PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"


@click.group()
def codecarbon():
    pass


@codecarbon.command("init", short_help="Create an experiment id in a public project.")
def init():
    experiment_id = get_existing_local_exp_id()
    new_local = False
    if experiment_id is None:
        api = ApiClient(endpoint_url=get_api_endpoint())
        experiment = ExperimentCreate(
            timestamp=get_datetime_with_timezone(),
            name="Code Carbon user test",
            description="Code Carbon user test with default project",
            on_cloud=False,
            project_id=DEFAULT_PROJECT_ID,
            country_name="France",
            country_iso_code="FRA",
            region="france",
        )
        experiment_id = api.add_experiment(experiment)
        write_local_exp_id(experiment_id)
        new_local = True

    click.echo(
        "\nWelcome to CodeCarbon, here is your experiment id:\n"
        + click.style(f"{experiment_id}", fg="bright_green")
        + (
            ""
            if new_local
            else " (from "
            + click.style("./.codecarbon.config", fg="bright_blue")
            + ")\n"
        )
    )
    if new_local:
        click.echo(
            "\nCodeCarbon automatically added this id to your local config: "
            + click.style("./.codecarbon.config", fg="bright_blue")
            + "\n"
        )


@codecarbon.command(
    "monitor",
    short_help="Run an infinite loop to monitor this machine.",
    help=f"""
    Monitor the environmental impact of programs.

    This command has two usages:

    Examples:

    \b
    # Monitor the system until you press CTRL-C
    {sys.argv[0]} monitor

    \b
    # Run and monitor a subprocess called "recon-all" and forward arguments to "recon-all":
    {sys.argv[0]} monitor -- recon-all -s sub-101 -i sub-101_ses-BL_T1w.nii.gz -all
    """,
)
@click.option(
    "--measure_power_secs", default=10, help="Interval between two measures. (10)"
)
@click.option(
    "--api_call_interval",
    default=30,
    help="Number of measures before calling API. (30).",
)
@click.option(
    "--api/--no-api", default=True, help="Choose to call Code Carbon API or not. (yes)"
)
@click.argument("cmd", nargs=-1)
def monitor(measure_power_secs, api_call_interval, api, cmd):
    experiment_id = get_existing_local_exp_id()
    if api and experiment_id is None:
        click.echo("ERROR: No experiment id, call 'codecarbon init' first.")
        sys.exit(1)

    if cmd:
        click.echo("CodeCarbon is going to run and monitor this command:")
        click.echo(f"\n\t{shlex.join(cmd)}\n")
        rc = monitor_subprocess(measure_power_secs, api_call_interval, api, cmd)
        sys.exit(rc)
    else:
        click.echo("CodeCarbon is going in an infinite loop to monitor this machine.")
        monitor_infinite_loop(measure_power_secs, api_call_interval, api)
