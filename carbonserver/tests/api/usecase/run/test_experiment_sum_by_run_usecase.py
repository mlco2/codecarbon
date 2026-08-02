from datetime import datetime, timedelta
from unittest import mock

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.usecases.run.experiment_sum_by_run import (
    ExperimentSumsByRunUsecase,
)

EXPERIMENT_ID = "2916fe6c-00a0-40b6-a3bd-ae9877661bdb"
END_DATE = datetime.now()
START_DATE = END_DATE - dateutil.relativedelta.relativedelta(months=3)

EMISSIONS_SUM = 152.28955200363455

EXPERIMENT_WITH_DETAILS = {
    "run_id": EXPERIMENT_ID,
    "timestamp": "2022-03-16T21:57:41.003455",
    "emissions": 152.28955200363455,
    "cpu_power": 5760,
    "gpu_power": 2983.9739999999993,
    "ram_power": 806.0337192959997,
    "cpu_energy": 191.8251863024175,
    "gpu_energy": 140.01098718681496,
    "ram_energy": 26.84332784201141,
    "energy_consumed": 358.6795013312438,
    "duration": 7673204,
    "emissions_rate": 1.0984556074701752,
    "emissions_count": 64,
}


class SessionContextMock:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        return None


def test_detailed_sum_computes_for_experiment_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    experiment_id = EXPERIMENT_ID
    experiment_sum_by_run_usecase = ExperimentSumsByRunUsecase(repository_mock)

    expected_emission_sum = EMISSIONS_SUM
    repository_mock.get_experiment_detailed_sums_by_run.return_value = [
        EXPERIMENT_WITH_DETAILS
    ]

    actual_experiment_sum_by_run = experiment_sum_by_run_usecase.compute_detailed_sum(
        experiment_id, START_DATE, END_DATE
    )

    assert actual_experiment_sum_by_run[0]["emissions"] == expected_emission_sum


def test_detailed_sum_with_max_points_buckets_result():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.get_experiment_bucketed_sums_by_run.return_value = [
        {"timestamp": START_DATE, "run_count": 1000}
    ]
    experiment_sum_by_run_usecase = ExperimentSumsByRunUsecase(repository_mock)

    actual = experiment_sum_by_run_usecase.compute_detailed_sum(
        EXPERIMENT_ID, START_DATE, END_DATE, max_points=300
    )

    assert actual == [{"timestamp": START_DATE, "run_count": 1000}]
    repository_mock.get_experiment_detailed_sums_by_run.assert_not_called()


def test_detailed_sum_uses_max_points_as_bucket_measure():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    experiment_sum_by_run_usecase = ExperimentSumsByRunUsecase(repository_mock)

    experiment_sum_by_run_usecase.compute_detailed_sum(
        EXPERIMENT_ID,
        datetime(2026, 1, 1),
        datetime(2026, 1, 1) + timedelta(seconds=1000),
        max_points=300,
    )

    repository_mock.get_experiment_bucketed_sums_by_run.assert_called_once_with(
        EXPERIMENT_ID,
        datetime(2026, 1, 1),
        datetime(2026, 1, 1) + timedelta(seconds=1000),
        300,
    )


def test_detailed_sum_query_excludes_runs_without_emissions_in_date_range():
    # Use the real repository with a mocked SQLAlchemy session context so this test
    # covers the join built by get_experiment_detailed_sums_by_run. Mocking the
    # repository itself would only test usecase pass-through and would not fail if
    # the query switched back to an outer join that returns null aggregate rows.
    session_mock = mock.Mock()
    query_mock = mock.Mock()
    session_mock.query.return_value = query_mock
    query_mock.join.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.group_by.return_value = query_mock
    query_mock.all.return_value = []

    session_factory_mock = mock.Mock(return_value=SessionContextMock(session_mock))
    repository = SqlAlchemyRepository(session_factory_mock)
    experiment_sum_by_run_usecase = ExperimentSumsByRunUsecase(repository)

    actual_experiment_sum_by_run = experiment_sum_by_run_usecase.compute_detailed_sum(
        EXPERIMENT_ID, START_DATE, END_DATE
    )

    assert actual_experiment_sum_by_run == []
    query_mock.join.assert_called_once()
    assert query_mock.join.call_args.kwargs.get("isouter", False) is False
