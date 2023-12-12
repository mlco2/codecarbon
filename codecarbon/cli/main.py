import sys
import time
from typing import Optional

import click
import questionary
import typer
from rich.prompt import Confirm
from typing_extensions import Annotated

from codecarbon import __app_name__, __version__
from codecarbon.cli.cli_utils import (
    get_api_endpoint,
    get_existing_local_exp_id,
    write_local_exp_id,
)
from codecarbon.core.api_client import ApiClient, get_datetime_with_timezone
from codecarbon.core.schemas import (
    ExperimentCreate,
    OrganizationCreate,
    ProjectCreate,
    TeamCreate,
)
from codecarbon.emissions_tracker import EmissionsTracker

DEFAULT_PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"
DEFAULT_ORGANIzATION_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"

codecarbon = typer.Typer()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@codecarbon.callback()
def main(
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


@codecarbon.command("init", short_help="Create an experiment id in a public project.")
def init():
    """
    Initialize CodeCarbon, this will prompt you for configuration of Organisation/Team/Project/Experiment.
    """
    typer.echo("Welcome to CodeCarbon configuration wizard")
    use_config = Confirm.ask(
        "Use existing /.codecarbonconfig to configure ?",
    )
    if use_config is True:
        experiment_id = get_existing_local_exp_id()
    else:
        experiment_id = None
    new_local = False
    if experiment_id is None:
        api_endpoint = get_api_endpoint()
        api_endpoint = typer.prompt(
            f"Default API endpoint is {api_endpoint}. You can change it in /.codecarbonconfig. Press enter to continue or input other url",
            type=str,
            default=api_endpoint,
        )
        api = ApiClient(endpoint_url=api_endpoint)
        organizations = api.get_list_organizations()
        org = questionary.select(
            "Pick existing organization from list or Create new organization ?",
            [org["name"] for org in organizations] + ["Create New Organization"],
        ).ask()

        if org == "Create New Organization":
            org_name = typer.prompt(
                "Organization name", default="Code Carbon user test"
            )
            org_description = typer.prompt(
                "Organization description", default="Code Carbon user test"
            )
            if org_name in organizations:
                typer.echo(
                    f"Organization {org_name} already exists, using it for this experiment."
                )
                organization = [orga for orga in organizations if orga["name"] == org][
                    0
                ]
            else:
                organization_create = OrganizationCreate(
                    name=org_name,
                    description=org_description,
                )
                organization = api.create_organization(organization=organization_create)
            typer.echo(f"Created organization : {organization}")
        else:
            organization = [orga for orga in organizations if orga["name"] == org][0]
        teams = api.list_teams_from_organization(organization["id"])

        team = questionary.select(
            "Pick existing team from list or create new team in organization ?",
            [team["name"] for team in teams] + ["Create New Team"],
        ).ask()
        if team == "Create New Team":
            team_name = typer.prompt("Team name", default="Code Carbon user test")
            team_description = typer.prompt(
                "Team description", default="Code Carbon user test"
            )
            team_create = TeamCreate(
                name=team_name,
                description=team_description,
                organization_id=organization["id"],
            )
            team = api.create_team(
                team=team_create,
            )
            typer.echo(f"Created team : {team}")
        else:
            team = [t for t in teams if t["name"] == team][0]
        projects = api.list_projects_from_team(team["id"])
        project = questionary.select(
            "Pick existing project from list or Create new project ?",
            [project["name"] for project in projects] + ["Create New Project"],
            default="Create New Project",
        ).ask()
        if project == "Create New Project":
            project_name = typer.prompt("Project name", default="Code Carbon user test")
            project_description = typer.prompt(
                "Project description", default="Code Carbon user test"
            )
            project_create = ProjectCreate(
                name=project_name,
                description=project_description,
                team_id=team["id"],
            )
            project = api.create_project(project=project_create)
            typer.echo(f"Created project : {project}")
        else:
            project = [p for p in projects if p["name"] == project][0]

        experiments = api.list_experiments_from_project(project["id"])
        experiment = questionary.select(
            "Pick existing experiment from list or Create new experiment ?",
            [experiment["name"] for experiment in experiments]
            + ["Create New Experiment"],
            default="Create New Experiment",
        ).ask()
        if experiment == "Create New Experiment":
            typer.echo("Creating new experiment")
            exp_name = typer.prompt(
                "Experiment name :", default="Code Carbon user test"
            )
            exp_description = typer.prompt(
                "Experiment description :",
                default="Code Carbon user test",
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
            country_name = typer.prompt("Country name :", default="France")
            country_iso_code = typer.prompt("Country ISO code :", default="FRA")
            region = typer.prompt("Region :", default="france")
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
            experiment_id = api.add_experiment(experiment=experiment_create)

        else:
            experiment_id = [e for e in experiments if e["name"] == experiment][0]["id"]

    write_to_config = Confirm.ask(
        "Write experiment_id to /.codecarbonconfig ? (Press enter to continue)"
    )

    if write_to_config is True:
        write_local_exp_id(experiment_id)
        new_local = True
    typer.echo(
        "\nCodeCarbon Initialization achieved, here is your experiment id:\n"
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
            "\nCodeCarbon added this id to your local config: "
            + click.style("./.codecarbon.config", fg="bright_blue")
            + "\n"
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
):
    """Monitor your machine's carbon emissions.

    Args:
        measure_power_secs (Annotated[int, typer.Argument, optional): Interval between two measures. Defaults to 10.
        api_call_interval (Annotated[int, typer.Argument, optional): Number of measures before calling API. Defaults to 30.
        api (Annotated[bool, typer.Option, optional): Choose to call Code Carbon API or not. Defaults to True.
    """
    experiment_id = get_existing_local_exp_id()
    if api and experiment_id is None:
        typer.echo("ERROR: No experiment id, call 'codecarbon init' first.")
        sys.exit(1)
    typer.echo("CodeCarbon is going in an infinite loop to monitor this machine.")
    with EmissionsTracker(
        measure_power_secs=measure_power_secs,
        api_call_interval=api_call_interval,
        save_to_api=api,
    ):
        # Infinite loop
        while True:
            time.sleep(300)


if __name__ == "__main__":
    codecarbon()
