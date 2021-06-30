import click
from codecarbon.core.api_client import ApiClient, get_datetime_with_timezone
from codecarbon.core.schemas import ExperimentCreate
from codecarbon.cli.cli_utils import get_existing_local_exp_id

DEFAULT_PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"


@click.group()
def codecarbon():
    pass


@codecarbon.command()
def init():
    experiment_id = get_existing_local_exp_id()
    if experiment_id is None:
        api = ApiClient()
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
    click.echo(f"Welcome to CodeCarbon, here is your experiment id : {experiment_id}")
