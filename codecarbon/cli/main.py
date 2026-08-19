import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.prompt import Confirm
from typing_extensions import Annotated

from codecarbon import __app_name__, __version__
from codecarbon.cli.cli_utils import (
    create_new_config_file,
    get_api_endpoint,
    get_config,
    get_existing_exp_id,
    overwrite_local_config,
)

API_URL = os.environ.get("API_URL", "https://dashboard.codecarbon.io/api")

DEFAULT_PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"
DEFAULT_ORGANIzATION_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"

codecarbon = typer.Typer(no_args_is_help=True)


def main():
    """
    Main entry point for the CodeCarbon CLI application.
    This function catches any exceptions raised during the execution of the CLI commands
    and prints an error message in red using Rich's print function.
    """
    try:
        codecarbon()
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {e}")
        raise sys.exit(1)


def _api_call(action: str, func, *args, **kwargs):
    """
    Run a call to the Code Carbon API, turning the errors it now raises into a
    readable message and a clean exit instead of a traceback.

    :action: what was being attempted, used as the first part of the message.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"[yellow]{action}[/yellow]. (error: {e})")
        raise typer.Exit(1)


def _version_callback(value: bool) -> None:
    if value:
        print(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@codecarbon.callback()
def version(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    return


def show_config(path: Path = Path("./.codecarbon.config")) -> None:
    from codecarbon.cli.auth import get_access_token
    from codecarbon.core.api_client import ApiClient

    d = get_config(path)
    print("Current configuration : \n")
    print("Config file content : ")
    print(d)
    try:
        api_endpoint = get_api_endpoint(path)
        api = ApiClient(endpoint_url=api_endpoint)
        api.set_access_token(get_access_token())
        if "organization_id" not in d:
            print(
                "No organization_id in config, follow setup instruction to complete your configuration file!",
            )
        else:
            org = api.get_organization(d["organization_id"])

            if "project_id" not in d:
                print(
                    "No project_id in config, follow setup instruction to complete your configuration file!",
                )
            else:
                project = api.get_project(d["project_id"])
                if "experiment_id" not in d:
                    print(
                        "No experiment_id in config, follow setup instruction to complete your configuration file!",
                    )
                else:
                    experiment = api.get_experiment(d["experiment_id"])
                    print("\nExperiment :")
                    print(experiment)
                    print("\nProject :")
                    print(project)
                    print("\nOrganization :")
                    print(org)
    except Exception as e:
        print(
            f"[yellow]Could not validate remote configuration details[/yellow]. You can continue with local configuration setup. (error: {e})"
        )


@codecarbon.command(
    "test-api", short_help="Make an authenticated GET request to an API endpoint"
)
def api_get():
    """
    ex: test-api
    """
    from codecarbon.cli.auth import get_access_token
    from codecarbon.core.api_client import ApiClient

    api_endpoint = get_api_endpoint()
    api = ApiClient(endpoint_url=api_endpoint)
    api.set_access_token(get_access_token())
    organizations = _api_call("API request failed", api.get_list_organizations)
    print(organizations)


@codecarbon.command("login", short_help="Login to CodeCarbon")
def login():
    from codecarbon.cli.auth import authorize, get_access_token
    from codecarbon.core.api_client import ApiClient

    authorize()
    api_endpoint = get_api_endpoint()
    api = ApiClient(endpoint_url=api_endpoint)
    access_token = get_access_token()
    api.set_access_token(access_token)
    _api_call("Authentication check failed", api.check_auth)


def get_api_key(project_id: str):
    import requests

    from codecarbon.cli.auth import get_access_token

    api_endpoint = get_api_endpoint()
    api_endpoint = api_endpoint.rstrip("/")
    req = requests.post(
        f"{api_endpoint}/projects/{project_id}/api-tokens",
        json={
            "project_id": project_id,
            "name": "api token",
            "x_token": "???",
        },
        headers={"Authorization": f"Bearer {get_access_token()}"},
    )
    req.raise_for_status()
    api_key = req.json()["token"]
    return api_key


@codecarbon.command("get-token", short_help="Get project token")
def get_token(project_id: str):
    # api = ApiClient(endpoint_url=API_URL) # TODO: get endpoint from config
    # api.set_access_token(get_access_token())
    token = get_api_key(project_id)
    print("Your token: " + token)
    print("Add it to the api_key field in your configuration file")


@codecarbon.command("config", short_help="Generate or show config")
def config():
    """
    Initialize CodeCarbon, this will prompt you for configuration of Organisation/Team/Project/Experiment.
    """
    from codecarbon.cli.auth import get_access_token
    from codecarbon.core.api_client import ApiClient, get_datetime_with_timezone
    from codecarbon.core.schemas import (
        ExperimentCreate,
        OrganizationCreate,
        ProjectCreate,
    )

    print("Welcome to CodeCarbon configuration wizard")
    home = Path.home()
    global_path = (home / ".codecarbon.config").expanduser().resolve()

    if global_path.exists():
        print("Existing global config file found :")
        show_config(global_path)

        use_config = questionary_prompt(
            "Use existing global ~/.codecarbon.config to configure or create a new file somewhere else ?",
            ["~/.codecarbon.config", "Create New Config"],
            default="~/.codecarbon.config",
        )

        if use_config == "~/.codecarbon.config":
            modify = Confirm.ask("Do you want to modify the existing config file ?")
            if modify:
                print(f"Modifying existing config file {global_path}:")
                file_path = global_path
            else:
                print(f"Using already existing global config file {global_path}")

                return
        else:
            file_path = create_new_config_file()
    else:
        file_path = create_new_config_file()

    api_endpoint = get_api_endpoint(file_path)
    api_endpoint = typer.prompt(
        f"Current API endpoint is {api_endpoint}. Press enter to continue or input other url",
        type=str,
        default=api_endpoint,
    )
    overwrite_local_config("api_endpoint", api_endpoint, path=file_path)
    api = ApiClient(endpoint_url=api_endpoint)
    api.set_access_token(get_access_token())
    organizations = _api_call(
        "Could not list organizations from API. Please check your login and API endpoint",
        api.get_list_organizations,
    )
    org = questionary_prompt(
        "Pick existing organization from list or Create new organization ?",
        [org["name"] for org in organizations] + ["Create New Organization"],
        default="Create New Organization",
    )

    if org == "Create New Organization":
        org_name = typer.prompt("Organization name", default="Code Carbon user test")
        org_description = typer.prompt(
            "Organization description", default="Code Carbon user test"
        )

        organization_create = OrganizationCreate(
            name=org_name,
            description=org_description,
        )
        organization = _api_call(
            "Could not create the organization",
            api.create_organization,
            organization=organization_create,
        )
        print(f"Created organization : {organization}")
    else:
        organization = [orga for orga in organizations if orga["name"] == org][0]
    org_id = organization["id"]
    overwrite_local_config("organization_id", org_id, path=file_path)

    projects = _api_call(
        "Could not list projects from API",
        api.list_projects_from_organization,
        org_id,
    )
    project_names = [project["name"] for project in projects]
    project = questionary_prompt(
        "Pick existing project from list or Create new project ?",
        project_names + ["Create New Project"],
        default="Create New Project",
    )
    if project == "Create New Project":
        project_name = typer.prompt("Project name", default="Code Carbon user test")
        project_description = typer.prompt(
            "Project description", default="Code Carbon user test"
        )
        project_create = ProjectCreate(
            name=project_name,
            description=project_description,
            organization_id=org_id,
        )
        project = _api_call(
            "Could not create the project", api.create_project, project=project_create
        )
        print(f"Created project : {project}")
    else:
        project = [p for p in projects if p["name"] == project][0]
    project_id = project["id"]
    overwrite_local_config("project_id", project_id, path=file_path)

    experiments = _api_call(
        "Could not list experiments from API",
        api.list_experiments_from_project,
        project_id,
    )
    experiments_names = [experiment["name"] for experiment in experiments]

    experiment = questionary_prompt(
        "Pick existing experiment from list or Create new experiment ?",
        experiments_names + ["Create New Experiment"],
        default="Create New Experiment",
    )
    if experiment == "Create New Experiment":
        print("Creating new experiment")
        exp_name = typer.prompt("Experiment name :", default="Code Carbon user test")
        exp_description = typer.prompt(
            "Experiment description :",
            default="Code Carbon user test ",
        )

        exp_on_cloud = Confirm.ask("Is this experiment running on the cloud ?")
        if exp_on_cloud is True:
            cloud_provider = typer.prompt(
                "Cloud provider (AWS, GCP, Azure, ...)", default="AWS"
            )
            cloud_region = typer.prompt(
                "Cloud region (eu-west-1, us-east-1, ...)", default="eu-west-1"
            )
        else:
            cloud_provider = None
            cloud_region = None
        country_name = typer.prompt("Country name :", default="Auto")
        country_iso_code = typer.prompt("Country ISO code :", default="Auto")
        region = typer.prompt("Region :", default="Auto")
        if country_name == "Auto":
            country_name = None
        if country_iso_code == "Auto":
            country_iso_code = None
        if region == "Auto":
            region = None
        experiment_create = ExperimentCreate(
            timestamp=get_datetime_with_timezone(),
            name=exp_name,
            description=exp_description,
            on_cloud=exp_on_cloud,
            project_id=project["id"],
            country_name=country_name,
            country_iso_code=country_iso_code,
            region=region,
            cloud_provider=cloud_provider,
            cloud_region=cloud_region,
        )
        experiment = _api_call(
            "Could not create the experiment",
            api.add_experiment,
            experiment=experiment_create,
        )

    else:
        experiment = [e for e in experiments if e["name"] == experiment][0]

    overwrite_local_config("experiment_id", experiment["id"], path=file_path)
    api_key = _api_call("Could not get the project API key", get_api_key, project_id)
    overwrite_local_config("api_key", api_key, path=file_path)
    show_config(file_path)
    print(
        "Consult [link=https://docs.codecarbon.io/latest/how-to/configuration/]configuration documentation[/link] for more configuration options"
    )


@codecarbon.command(
    "monitor",
    short_help="Monitor your machine's carbon emissions.",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def monitor(
    ctx: typer.Context,
    measure_power_secs: Annotated[
        int,
        typer.Option(help="Interval between two measures."),
    ] = 10,
    api_call_interval: Annotated[
        int,
        typer.Option(help="Number of measures between API calls."),
    ] = 30,
    api: Annotated[
        bool,
        typer.Option(help="Choose to call Code Carbon API or not"),
    ] = True,
    offline: Annotated[bool, typer.Option(help="Run in offline mode")] = False,
    country_iso_code: Annotated[
        str,
        typer.Option(help="3-letter country ISO code for offline mode"),
    ] = None,
    region: Annotated[
        str,
        typer.Option(help="Region/province for offline mode"),
    ] = None,
    log_level: Annotated[
        str,
        typer.Option(help="Log level (critical, error, warning, info, debug)"),
    ] = "error",
    project_name: Annotated[
        str,
        typer.Option(help="Project name for the current experiment run."),
    ] = None,
    output_dir: Annotated[
        str,
        typer.Option(help="Directory to write emissions.csv to."),
    ] = None,
    pue: Annotated[
        float,
        typer.Option(help="Power Usage Effectiveness of the datacenter."),
    ] = None,
    wue: Annotated[
        float,
        typer.Option(help="Water Usage Effectiveness of the datacenter."),
    ] = None,
    gpu_ids: Annotated[
        str,
        typer.Option(help="Comma-separated list of GPU ids to track, e.g. '0,1'."),
    ] = None,
    force_cpu_power: Annotated[
        int,
        typer.Option(help="Force CPU power draw in Watts instead of estimating it."),
    ] = None,
    force_ram_power: Annotated[
        int,
        typer.Option(help="Force RAM power draw in Watts instead of estimating it."),
    ] = None,
    allow_multiple_runs: Annotated[
        bool,
        typer.Option(
            help="Allow multiple codecarbon trackers to run at the same time on this machine."
        ),
    ] = None,
):
    """Monitor your machine's carbon emissions."""

    # Shared tracker args so monitor and run_and_monitor behave the same.
    # Options left at their default (None) are omitted so EmissionsTracker
    # can still fall back to its own config-file / environment-variable
    # defaults instead of having them silently overridden by None here.
    tracker_args = {
        "measure_power_secs": measure_power_secs,
        "api_call_interval": api_call_interval,
        "log_level": log_level,
    }
    optional_args = {
        "project_name": project_name,
        "output_dir": output_dir,
        "pue": pue,
        "wue": wue,
        "gpu_ids": [g.strip() for g in gpu_ids.split(",")] if gpu_ids else None,
        "force_cpu_power": force_cpu_power,
        "force_ram_power": force_ram_power,
        "allow_multiple_runs": allow_multiple_runs,
    }
    tracker_args.update({k: v for k, v in optional_args.items() if v is not None})
    # Set up the tracker arguments based on mode (offline vs online) and validate required args for each mode
    if offline:
        if not country_iso_code:
            print(
                "ERROR: Country ISO code is required for offline mode. Add it to your configuration or provide it via the command line: `--country-iso-code FRA`",
                file=sys.stderr,
            )
            raise typer.Exit(1)

        tracker_args = {
            **tracker_args,
            "country_iso_code": country_iso_code,
            "region": region,
        }
    else:
        experiment_id = get_existing_exp_id()
        if api and experiment_id is None:
            print(
                "ERROR: No experiment id. Set CODECARBON_EXPERIMENT_ID, call 'codecarbon config' first, or run in offline mode with `--offline --country-iso-code FRA`.",
                file=sys.stderr,
            )
            raise typer.Exit(1)

        tracker_args = {**tracker_args, "save_to_api": api}

    from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker

    # If extra args are provided (e.g. `codecarbon monitor -- my_script.py`), delegate to `run_and_monitor`
    if getattr(ctx, "args", None):
        from codecarbon.cli.monitor import run_and_monitor

        return run_and_monitor(ctx, offline=offline, **tracker_args)

    # Instantiate the tracker
    if offline:
        tracker = OfflineEmissionsTracker(**tracker_args)
    else:
        tracker = EmissionsTracker(**tracker_args)

    def signal_handler(signum, frame):
        print("\nReceived signal to stop. Saving emissions data...")
        tracker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("CodeCarbon is going in an infinite loop to monitor this machine.")
    print("Press Ctrl+C to stop and save emissions data.")

    tracker.start()
    try:
        while True:
            if (
                hasattr(tracker, "_another_instance_already_running")
                and tracker._another_instance_already_running
            ):
                print("Another instance of CodeCarbon is already running. Exiting.")
                break
            time.sleep(300)
    except Exception as e:
        print(f"\nError occurred: {e}")
        tracker.stop()
        raise e


@codecarbon.command("detect", short_help="Detect hardware and print information.")
def detect():
    """
    Detects hardware and prints information without running any measurements.
    """
    from codecarbon.emissions_tracker import EmissionsTracker

    print("Detecting hardware...")
    tracker = EmissionsTracker(save_to_file=False)
    hardware_info = tracker.get_detected_hardware()

    print("\nDetected Hardware and System Information:")
    print(f"- Available RAM: {hardware_info['ram_total_size']:.3f} GB")
    print(
        f"- CPU count: {hardware_info['cpu_count']} thread(s) in {hardware_info['cpu_physical_count']} physical CPU(s)"
    )
    print(f"- CPU model: {hardware_info['cpu_model']}")
    print(f"- GPU count: {hardware_info['gpu_count']}")

    gpu_model_str = hardware_info["gpu_model"]
    if hardware_info.get("gpu_ids"):
        gpu_model_str += (
            f" BUT only tracking these GPU ids : {hardware_info['gpu_ids']}"
        )
    print(f"- GPU model: {gpu_model_str}")


@codecarbon.command(
    "report",
    short_help="Generate a summary report from emissions data.",
)
def report(
    file: Annotated[
        str,
        typer.Option(
            "--file",
            "-f",
            help="Path to the emissions CSV file.",
        ),
    ] = "emissions.csv",
    project: Annotated[
        Optional[str],
        typer.Option(
            "--project",
            "-p",
            help="Filter results by project name.",
        ),
    ] = None,
    format_output: Annotated[
        str,
        typer.Option(
            "--format",
            help="Output format: 'rich' (default) or 'json'.",
        ),
    ] = "rich",
):
    """
    Generate a summary report from existing emissions data.

    Reads an emissions CSV file (produced by CodeCarbon's tracker) and
    displays aggregate statistics with real-world equivalences.

    Examples::

        codecarbon report
        codecarbon report --file path/to/emissions.csv
        codecarbon report --project my_project
        codecarbon report --format json
    """
    import json as json_mod

    import pandas as pd
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from codecarbon.core.equivalences import EmissionsEquivalences

    console = Console()

    if not os.path.isfile(file):
        console.print(
            f"[bold red]Error:[/bold red] File '{file}' not found. "
            "Run CodeCarbon tracker first to generate emissions data, or "
            "specify a file with --file.",
        )
        raise typer.Exit(1)

    try:
        df = pd.read_csv(file)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not read '{file}': {e}")
        raise typer.Exit(1)

    if df.empty:
        console.print(
            f"[bold yellow]Warning:[/bold yellow] File '{file}' contains no data."
        )
        raise typer.Exit(0)

    if project:
        if "project_name" not in df.columns:
            console.print(
                "[bold red]Error:[/bold red] CSV file has no 'project_name' column."
            )
            raise typer.Exit(1)
        df = df[df["project_name"] == project]
        if df.empty:
            console.print(
                f"[bold yellow]Warning:[/bold yellow] No data found for project '{project}'."
            )
            raise typer.Exit(0)

    # Compute aggregate statistics
    summary = _compute_summary(df)

    # Compute equivalences
    eq_engine = EmissionsEquivalences()
    equivalences = eq_engine.compute(summary["total_emissions_kg"])

    if format_output == "json":
        output = {
            "summary": summary,
            "equivalences": equivalences.to_dict(),
        }
        console.print(json_mod.dumps(output, indent=2, default=str))
        return

    # Rich formatted output
    console.print()
    console.print(
        Panel(
            "[bold green]CodeCarbon Emissions Report[/bold green]",
            expand=False,
        )
    )

    # Summary table
    summary_table = Table(title="📊 Emissions Summary", show_lines=True)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green", justify="right")

    summary_table.add_row(
        "Total CO₂ Emissions",
        _format_emissions(summary["total_emissions_kg"]),
    )
    summary_table.add_row(
        "Total Energy Consumed",
        f"{summary['total_energy_kwh']:.6f} kWh",
    )
    summary_table.add_row(
        "Total Duration",
        _format_duration(summary["total_duration_s"]),
    )
    if summary.get("total_water_l", 0) > 0:
        summary_table.add_row(
            "Total Water Consumed",
            f"{summary['total_water_l']:.4f} L",
        )
    summary_table.add_row("Number of Runs", str(summary["num_runs"]))
    if summary["num_projects"] > 1:
        summary_table.add_row("Number of Projects", str(summary["num_projects"]))

    console.print(summary_table)

    # Per-project breakdown (if multiple projects)
    if summary["num_projects"] > 1 and "project_name" in df.columns:
        project_table = Table(title="📁 Per-Project Breakdown", show_lines=True)
        project_table.add_column("Project", style="cyan")
        project_table.add_column("Runs", style="white", justify="right")
        project_table.add_column("Emissions", style="green", justify="right")
        project_table.add_column("Energy (kWh)", style="yellow", justify="right")

        for proj_name, proj_df in df.groupby("project_name"):
            proj_emissions = proj_df["emissions"].sum() if "emissions" in proj_df.columns else 0
            proj_energy = proj_df["energy_consumed"].sum() if "energy_consumed" in proj_df.columns else 0
            project_table.add_row(
                str(proj_name),
                str(len(proj_df)),
                _format_emissions(proj_emissions),
                f"{proj_energy:.6f}",
            )
        console.print(project_table)

    # Equivalences panel
    console.print()
    eq_table = Table(title="🌍 Real-World Equivalences", show_lines=True)
    eq_table.add_column("Equivalence", style="cyan")
    eq_table.add_column("Value", style="green", justify="right")

    eq_table.add_row("🚗 Car travel", f"{equivalences.car_km:.1f} km")
    eq_table.add_row("✈️  Flights (CDG→JFK)", f"{equivalences.flights_paris_nyc:.4f} one-way")
    eq_table.add_row("📺 TV watching", f"{equivalences.tv_hours:.1f} hours")
    eq_table.add_row("📱 Smartphone charges", f"{equivalences.smartphone_charges:.0f} charges")
    if equivalences.tree_months >= 12:
        eq_table.add_row("🌳 Tree offset", f"{equivalences.tree_months / 12:.2f} tree-years")
    else:
        eq_table.add_row("🌳 Tree offset", f"{equivalences.tree_months:.2f} tree-months")
    eq_table.add_row("🏠 US household weekly", f"{equivalences.household_percentage:.4f}%")
    eq_table.add_row("💡 LED bulb (10W)", f"{equivalences.led_bulb_hours:.1f} hours")
    eq_table.add_row("🎬 HD streaming", f"{equivalences.streaming_hours:.1f} hours")

    console.print(eq_table)
    console.print()


def _compute_summary(df) -> dict:
    """Compute aggregate summary statistics from an emissions DataFrame."""
    summary = {
        "num_runs": len(df),
        "num_projects": df["project_name"].nunique() if "project_name" in df.columns else 1,
        "total_emissions_kg": df["emissions"].sum() if "emissions" in df.columns else 0,
        "total_energy_kwh": df["energy_consumed"].sum() if "energy_consumed" in df.columns else 0,
        "total_duration_s": df["duration"].sum() if "duration" in df.columns else 0,
        "total_water_l": df["water_consumed"].sum() if "water_consumed" in df.columns else 0,
    }

    # Average power values
    for power_col in ["cpu_power", "gpu_power", "ram_power"]:
        if power_col in df.columns:
            summary[f"avg_{power_col}_w"] = df[power_col].mean()

    return summary


def _format_emissions(kg: float) -> str:
    """Format emissions with appropriate unit (g, kg, or tonnes)."""
    if kg >= 1000:
        return f"{kg / 1000:.3f} tonnes CO₂eq"
    if kg >= 1:
        return f"{kg:.4f} kg CO₂eq"
    return f"{kg * 1000:.4f} g CO₂eq"


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    if seconds < 3600:
        return f"{seconds / 60:.1f} minutes"
    if seconds < 86400:
        return f"{seconds / 3600:.1f} hours"
    return f"{seconds / 86400:.1f} days"


def questionary_prompt(prompt, list_options, default):
    import questionary

    value = questionary.select(
        prompt,
        list_options,
        default,
    ).ask()
    return value


if __name__ == "__main__":
    main()
