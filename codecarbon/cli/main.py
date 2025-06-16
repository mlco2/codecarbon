import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import questionary
import requests
import typer
from fief_client import Fief
from fief_client.integrations.cli import FiefAuth
from rich import print
from rich.prompt import Confirm
from typing_extensions import Annotated

from codecarbon import __app_name__, __version__
from codecarbon.cli.cli_utils import (
    create_new_config_file,
    get_api_endpoint,
    get_config,
    get_existing_local_exp_id,
    overwrite_local_config,
)
from codecarbon.core.api_client import ApiClient, get_datetime_with_timezone
from codecarbon.core.schemas import ExperimentCreate, OrganizationCreate, ProjectCreate
from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker

AUTH_CLIENT_ID = os.environ.get(
    "AUTH_CLIENT_ID",
    "jsUPWIcUECQFE_ouanUuVhXx52TTjEVcVNNtNGeyAtU",
)
AUTH_SERVER_URL = os.environ.get(
    "AUTH_SERVER_URL", "https://auth.codecarbon.io/codecarbon"
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
    d = get_config(path)
    api_endpoint = get_api_endpoint(path)
    api = ApiClient(endpoint_url=api_endpoint)
    api.set_access_token(_get_access_token())
    print("Current configuration : \n")
    print("Config file content : ")
    print(d)
    try:
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
        raise ValueError(
            f"Your configuration is invalid, please verify your configuration file at {path}. To start from scratch, run `codecarbon config` and overwrite your configuration file. (error: {e})"
        )


def get_fief_auth():
    fief = Fief(AUTH_SERVER_URL, AUTH_CLIENT_ID)
    fief_auth = FiefAuth(fief, "./credentials.json")
    return fief_auth


def _get_access_token():
    try:
        access_token_info = get_fief_auth().access_token_info()
        access_token = access_token_info["access_token"]
        return access_token
    except Exception as e:
        raise ValueError(
            f"Not able to retrieve the access token, please run `codecarbon login` first! (error: {e})"
        )


def _get_id_token():
    id_token = get_fief_auth()._tokens["id_token"]
    return id_token


@codecarbon.command(
    "test-api", short_help="Make an authenticated GET request to an API endpoint"
)
def api_get():
    """
    ex: test-api
    """
    api = ApiClient(endpoint_url=API_URL)  # TODO: get endpoint from config
    api.set_access_token(_get_access_token())
    organizations = api.get_list_organizations()
    print(organizations)


@codecarbon.command("login", short_help="Login to CodeCarbon")
def login():
    get_fief_auth().authorize()
    api = ApiClient(endpoint_url=API_URL)  # TODO: get endpoint from config
    access_token = _get_access_token()
    api.set_access_token(access_token)
    api.check_auth()


def get_api_key(project_id: str):
    req = requests.post(
        f"{API_URL}/projects/{project_id}/api-tokens",
        json={
            "project_id": project_id,
            "name": "api token",
            "x_token": "???",
        },
        headers={"Authorization": f"Bearer {_get_access_token()}"},
    )
    api_key = req.json()["token"]
    return api_key


@codecarbon.command("get-token", short_help="Get project token")
def get_token(project_id: str):
    # api = ApiClient(endpoint_url=API_URL) # TODO: get endpoint from config
    # api.set_access_token(_get_access_token())
    token = get_api_key(project_id)
    print("Your token: " + token)
    print("Add it to the api_key field in your configuration file")


@codecarbon.command("config", short_help="Generate or show config")
def config():
    """
    Initialize CodeCarbon, this will prompt you for configuration of Organisation/Team/Project/Experiment.
    """

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
    api.set_access_token(_get_access_token())
    organizations = api.get_list_organizations()
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
        organization = api.create_organization(organization=organization_create)
        if organization is None:
            print("Error creating organization")
            return
        print(f"Created organization : {organization}")
    else:
        organization = [orga for orga in organizations if orga["name"] == org][0]
    org_id = organization["id"]
    overwrite_local_config("organization_id", org_id, path=file_path)

    projects = api.list_projects_from_organization(org_id)
    project_names = [project["name"] for project in projects] if projects else []
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
        project = api.create_project(project=project_create)
        print(f"Created project : {project}")
    else:
        project = [p for p in projects if p["name"] == project][0]
    project_id = project["id"]
    overwrite_local_config("project_id", project_id, path=file_path)

    experiments = api.list_experiments_from_project(project_id)
    experiments_names = (
        [experiment["name"] for experiment in experiments] if experiments else []
    )

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
        experiment = api.add_experiment(experiment=experiment_create)

    else:
        experiment = [e for e in experiments if e["name"] == experiment][0]

    overwrite_local_config("experiment_id", experiment["id"], path=file_path)
    api_key = get_api_key(project_id)
    overwrite_local_config("api_key", api_key, path=file_path)
    show_config(file_path)
    print(
        "Consult [link=https://mlco2.github.io/codecarbon/usage.html#configuration]configuration documentation[/link] for more configuration options"
    )


@codecarbon.command("monitor", short_help="Monitor your machine's carbon emissions.")
def monitor(
    measure_power_secs: Annotated[
        int, typer.Argument(help="Interval between two measures.")
    ] = 10,
    api_call_interval: Annotated[
        int, typer.Argument(help="Number of measures between API calls.")
    ] = 30,
    api: Annotated[
        bool, typer.Option(help="Choose to call Code Carbon API or not")
    ] = True,
    offline: Annotated[bool, typer.Option(help="Run in offline mode")] = False,
    country_iso_code: Annotated[
        str, typer.Option(help="3-letter country ISO code for offline mode")
    ] = None,
    region: Annotated[
        str, typer.Option(help="Region/province for offline mode")
    ] = None,
):
    """Monitor your machine's carbon emissions."""
    if offline:
        if not country_iso_code:
            print(
                "ERROR: country_iso_code is required for offline mode", file=sys.stderr
            )
            raise typer.Exit(1)

        tracker = OfflineEmissionsTracker(
            measure_power_secs=measure_power_secs,
            country_iso_code=country_iso_code,
            region=region,
        )
    else:
        experiment_id = get_existing_local_exp_id()
        if api and experiment_id is None:
            print(
                "ERROR: No experiment id, call 'codecarbon config' first.",
                file=sys.stderr,
            )
            raise typer.Exit(1)

        tracker = EmissionsTracker(
            measure_power_secs=measure_power_secs,
            api_call_interval=api_call_interval,
            save_to_api=api,
        )

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


def questionary_prompt(prompt, list_options, default):
    value = questionary.select(
        prompt,
        list_options,
        default,
    ).ask()
    return value


if __name__ == "__main__":
    main()
