import pytest

from carbonserver.database.schemas import ExperimentCreate, Experiment as SchemaExperiment
from carbonserver.database.models import Experiment as ModelExperiment

from carbonserver.api.infra.repositories.repository_experiment import InMemoryRepository


@pytest.fixture()
def experiments_repository():
    repo = InMemoryRepository()
    return repo


@pytest.fixture()
def experiments_fixture() -> ExperimentCreate:
    experiment = ExperimentCreate.parse_obj(
        {
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": 'experiment',
            "description": 'Test experiment',
            "is_active": True,
            "project_id": 1
        }
    )
    return experiment


@pytest.fixture()
def model_experiment() -> ModelExperiment:
    model_experiment = ModelExperiment(
        **{
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": 'experiment',
            "description": 'Test experiment',
            "is_active": True,
            "project_id": 1
        }
    )
    return model_experiment


def test_experiment_repository_saves_correct_experiment(
    experiments_repository, model_experiment
):
    experiment = ExperimentCreate.parse_obj(
        {
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": 'experiment',
            "description": 'Test experiment',
            "is_active": True,
            "project_id": 1
        }
    )
    experiments_repository.save_experiment(experiment)
    saved_experiments = experiments_repository.experiments
    assert len(saved_experiments) == 1
    assert saved_experiments[0].id == 1


def test_get_one_experiment_returns_the_correct_experiment_from_experiment_id(
    experiments_repository, experiments_fixture
):
    experiment_id = 1
    expected_experiment = SchemaExperiment.parse_obj(
        {
            "id": 1,
            "timestamp": "2021-04-04T08:43:00+02:00",
            "name": 'experiment',
            "description": 'Test experiment',
            "is_active": True,
            "project_id": 1
        }
    )
    experiments_repository.save_experiment(experiments_fixture)

    actual_experiment = experiments_repository.get_one_experiment(experiment_id)
    print(actual_experiment)
    assert expected_experiment == actual_experiment


def test_get_one_experiment_returns_the_correct_experiment_list_from_experiment_id(
    experiments_repository, experiments_fixture
):
    experiment_id = 1
    expected_emissions = [
        SchemaExperiment.parse_obj(
            {
                "id": 1,
                "timestamp": "2021-04-04T08:43:00+02:00",
                "name": 'experiment',
                "description": 'Test experiment',
                "is_active": True,
                "project_id": 1
            }
        )
    ]
    experiments_repository.save_experiment(experiments_fixture)

    actual_emissions = experiments_repository.get_experiments_from_experiment(experiment_id)

    assert expected_emissions == actual_emissions
