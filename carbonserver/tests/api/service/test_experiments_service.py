from unittest import mock

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import Experiment, ExperimentCreate
from carbonserver.api.services.experiments_service import ExperimentService

EXPERIMENT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EXPERIMENT_ID_2 = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"


EXPERIMENT_1 = Experiment(
    id=EXPERIMENT_ID,
    name="Experiment",
    description="Description",
    timestamp="2021-04-04T08:43:00+02:00",
    country_name="France",
    country_iso_code="France",
    region="Berry",
    on_cloud=True,
    cloud_provider="AWS",
    cloud_region="aws-east-1",
    project_id=PROJECT_ID,
)

EXPERIMENT_2 = Experiment(
    id=EXPERIMENT_ID_2,
    name="Experiment",
    description="Description",
    timestamp="2021-04-04T08:43:00+02:00",
    country_name="France",
    country_iso_code="France",
    region="Berry",
    on_cloud=True,
    cloud_provider="AWS",
    cloud_region="aws-east-1",
    project_id=PROJECT_ID,
)


@mock.patch("uuid.uuid4", return_value=EXPERIMENT_ID)
def test_emission_service_creates_correct_emission(_):
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = EXPERIMENT_ID
    experiment_service: ExperimentService = ExperimentService(repository_mock)
    repository_mock.add_experiment.return_value = EXPERIMENT_ID

    experiment_to_create = ExperimentCreate(
        name="Experiment",
        description="Description",
        timestamp="2021-04-04T08:43:00+02:00",
        country_name="France",
        country_iso_code="France",
        region="Berry",
        on_cloud=True,
        cloud_provider="AWS",
        cloud_region="aws-east-1",
        project_id=PROJECT_ID,
    )

    actual_saved_emission_id = experiment_service.add_experiment(experiment_to_create)

    assert actual_saved_emission_id == expected_id


def test_emission_service_retrieves_all_existing_emissions_for_one_run():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_experiments_ids = [EXPERIMENT_ID, EXPERIMENT_ID_2]
    emission_service: ExperimentService = ExperimentService(repository_mock)
    repository_mock.get_experiments_from_project.return_value = [
        EXPERIMENT_1,
        EXPERIMENT_2,
    ]

    experiments_list = emission_service.get_experiments_from_project(PROJECT_ID)
    actual_experiments_ids_list = map(lambda x: x.id, iter(experiments_list))
    diff = set(actual_experiments_ids_list) ^ set(expected_experiments_ids)

    assert not diff
    assert len(list(actual_experiments_ids_list)) == len(
        set(actual_experiments_ids_list)
    )


def test_emission_service_retrives_correct_emission_by_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_emission_id = EXPERIMENT_ID
    experiment_service: ExperimentService = ExperimentService(repository_mock)
    repository_mock.get_one_experiment.return_value = EXPERIMENT_1

    actual_emission = experiment_service.get_one_experiment(EXPERIMENT_ID)

    assert actual_emission.id == expected_emission_id
