from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate
from carbonserver.api.services.run_service import RunService

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"

EXPERIMENT_ID = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
EXPERIMENT_ID_2 = UUID("e395767d-0255-40f3-a314-5d2e01f56fbd")

RUN_ID = UUID("c13e851f-5c2f-403d-98d0-51fe15df3bc3")
RUN_ID_2 = UUID("dd011783-7d05-4376-ab60-9537738be25f")

RUN_1 = Run(
    id=RUN_ID,
    timestamp="2021-04-04T08:43:00+02:00",
    experiment_id=EXPERIMENT_ID,
)

RUN_2 = Run(
    id=RUN_ID_2,
    timestamp="2021-04-04T08:43:00+02:00",
    experiment_id=EXPERIMENT_ID_2,
)


@mock.patch("uuid.uuid4", return_value=RUN_ID)
def test_run_service_creates_correct_run(_):

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = RUN_ID
    run_service: RunService = RunService(repository_mock)
    repository_mock.add_run.return_value = RUN_1
    run_to_create = RunCreate(
        id=RUN_ID,
        timestamp="2021-04-04T08:43:00+02:00",
        experiment_id=EXPERIMENT_ID,
    )

    actual_saved_run = run_service.add_run(run_to_create)

    repository_mock.add_run.assert_called_with(run_to_create)
    assert actual_saved_run.id == expected_id


def test_run_service_retrieves_all_existing_runs():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_run_ids_list = [RUN_ID, RUN_ID_2]
    run_service: RunService = RunService(repository_mock)
    repository_mock.list_runs.return_value = [RUN_1, RUN_2]

    run_list = run_service.list_runs()
    actual_run_ids_list = map(lambda x: x.id, iter(run_list))
    diff = set(actual_run_ids_list) ^ set(expected_run_ids_list)

    assert not diff
    assert len(run_list) == len(expected_run_ids_list)


def test_run_service_retrieves_correct_run_by_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_org: Run = RUN_1
    run_service: RunService = RunService(repository_mock)
    repository_mock.get_one_run.return_value = RUN_1

    actual_saved_org = run_service.read_run(RUN_ID)

    assert actual_saved_org.id == expected_org.id


def test_run_service_retrieves_correct_run_by_experiment_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_experiment_id = EXPERIMENT_ID
    run_service: RunService = RunService(repository_mock)
    repository_mock.get_runs_from_experiment.return_value = [RUN_1]

    actual_runs = run_service.list_runs_from_experiment(EXPERIMENT_ID)

    assert actual_runs[0].experiment_id == expected_experiment_id
