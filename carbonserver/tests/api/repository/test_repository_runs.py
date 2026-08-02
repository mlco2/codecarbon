from datetime import datetime
from unittest import mock
from uuid import UUID

import dateutil.relativedelta

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository

EXPERIMENT_ID = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")


class SessionContextMock:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        return None


def test_experiment_detailed_sums_by_run_excludes_runs_without_emissions_in_date_range():
    # The repository opens sessions with `with self.session_factory() as session`.
    # This context mock lets us exercise the real query builder without needing a
    # live database, and catches a regression to an outer join that would return
    # runs with null aggregate fields.
    session_mock = mock.Mock()
    query_mock = mock.Mock()
    session_mock.query.return_value = query_mock
    query_mock.join.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.group_by.return_value = query_mock
    query_mock.all.return_value = []

    session_factory_mock = mock.Mock(return_value=SessionContextMock(session_mock))
    repository = SqlAlchemyRepository(session_factory_mock)

    end_date = datetime.now()
    start_date = end_date - dateutil.relativedelta.relativedelta(months=3)

    actual_run_sums = repository.get_experiment_detailed_sums_by_run(
        EXPERIMENT_ID, start_date, end_date
    )

    assert actual_run_sums == []
    query_mock.join.assert_called_once()
    assert query_mock.join.call_args.kwargs.get("isouter", False) is False
