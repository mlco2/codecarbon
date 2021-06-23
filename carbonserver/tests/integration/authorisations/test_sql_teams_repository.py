import pytest

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)


@pytest.fixture()
def organizations_repository():
    repo = SqlAlchemyRepository()
    return repo


@pytest.fixture()
def teams_repository():
    repo = SqlAlchemyRepository()
    return repo
