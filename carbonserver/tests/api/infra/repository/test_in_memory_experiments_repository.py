import pytest

from carbonserver.api.infra.repositories.repository_experiments import (
    InMemoryRepository,
)
from carbonserver.api.schemas import Experiment as SchemaExperiment
from carbonserver.api.schemas import ExperimentCreate
from carbonserver.database.sql_models import Experiment as ModelExperiment


@pytest.fixture()
def experiments_repository():
    repo = InMemoryRepository()
    return repo


@pytest.fixture()
def experiments_fixture() -> ExperimentCreate:
    experiment = ExperimentCreate.parse_obj(
        {
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": "experiment",
            "description": "Test experiment",
            "country_name": "France",
            "country_iso_code": "FRA",
            "region": "FRA",
            "on_cloud": True,
            "cloud_provider": "AWS",
            "cloud_region": "eu-west-1a",
            "project_id": 1,
        }
    )
    return experiment


@pytest.fixture()
def model_experiment() -> ModelExperiment:
    model_experiment = ModelExperiment(
        **{
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": "experiment",
            "description": "Test experiment",
            "country_name": "France",
            "country_iso_code": "FRA",
            "region": "FRA",
            "on_cloud": True,
            "cloud_provider": "AWS",
            "cloud_region": "eu-west-1a",
            "project_id": "1",
        }
    )
    return model_experiment


def test_experiment_repository_saves_correct_experiment(
    experiments_repository, model_experiment
):
    experiment = ExperimentCreate.parse_obj(
        {
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": "experiment",
            "description": "Test experiment",
            "country_name": "France",
            "country_iso_code": "FRA",
            "region": "FRA",
            "on_cloud": True,
            "cloud_provider": "AWS",
            "cloud_region": "eu-west-1a",
            "project_id": "1",
        }
    )
    experiments_repository.add_experiment(experiment)
    saved_experiments = experiments_repository.experiments
    assert len(saved_experiments) == 1
    assert saved_experiments[0].id == 1


def test_get_one_experiment_returns_the_correct_experiment_from_experiment_id(
    experiments_repository, experiments_fixture
):
    experiment_id = "1"
    expected_experiment = SchemaExperiment.parse_obj(
        {
            "id": "1",
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": "experiment",
            "description": "Test experiment",
            "country_name": "France",
            "country_iso_code": "FRA",
            "region": "FRA",
            "on_cloud": True,
            "cloud_provider": "AWS",
            "cloud_region": "eu-west-1a",
            "project_id": "1",
        }
    )
    experiments_repository.add_experiment(experiments_fixture)

    actual_experiment = experiments_repository.get_one_experiment(experiment_id)
    print(actual_experiment)
    assert expected_experiment == actual_experiment


def test_get_one_experiment_returns_the_correct_experiment_list_from_experiment_id(
    experiments_repository, experiments_fixture
):
    project_id = "3"
    expected_emissions = [
        SchemaExperiment.parse_obj(
            {
                "id": "133742",
                "timestamp": "2021-04-04T08:43:00+02:00",
                "name": "experiment",
                "description": "Test experiment",
                "country_name": "France",
                "country_iso_code": "FRA",
                "region": "FRA",
                "on_cloud": True,
                "cloud_provider": "AWS",
                "cloud_region": "eu-west-1a",
                "project_id": project_id,
            }
        )
    ]
    experiments_repository.add_experiment(expected_emissions[0])

    actual_emissions = experiments_repository.get_experiments_from_project(project_id)
    actual_emissions[0].id = expected_emissions[0].id
    assert expected_emissions == actual_emissions
