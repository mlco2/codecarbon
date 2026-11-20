from types import SimpleNamespace
from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import OrganizationWithRole

ORG_ID_1 = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")
ORG_ID_2 = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")


class SessionContextMock:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        return None


def test_list_organizations_tells_which_ones_the_user_administers():
    # The webapp groups the organizations menu on `is_admin`, so it must come from
    # the user's membership row rather than one member-list request per organization.
    session_mock = mock.Mock()
    query_mock = mock.Mock()
    session_mock.query.return_value = query_mock
    query_mock.join.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [
        (SimpleNamespace(id=ORG_ID_1, name="Owned", description="d1"), True),
        (SimpleNamespace(id=ORG_ID_2, name="Invited", description="d2"), False),
    ]
    session_factory_mock = mock.Mock(return_value=SessionContextMock(session_mock))
    repository = SqlAlchemyRepository(session_factory_mock)

    organizations = repository.list_organizations(user=SimpleNamespace(id="u1"))

    assert organizations == [
        OrganizationWithRole(
            id=ORG_ID_1, name="Owned", description="d1", is_admin=True
        ),
        OrganizationWithRole(
            id=ORG_ID_2, name="Invited", description="d2", is_admin=False
        ),
    ]


def test_list_organizations_is_empty_without_a_user():
    repository = SqlAlchemyRepository(mock.Mock())

    assert repository.list_organizations(user=None) == []
