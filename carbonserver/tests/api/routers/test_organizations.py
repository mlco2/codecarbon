from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import organizations
from carbonserver.database.sql_models import Organization as ModelOrganization

ORG_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_TO_CREATE = {
    "name": "Justice League",
    "description": "Collection of super heroes",
}

ORG_1 = {
    "id": ORG_ID_1,
    "name": "Justice League",
    "description": "Collection of super heroes",
    "teams": [],
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[organizations])
    app = FastAPI()
    app.container = container
    app.include_router(organizations.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_org(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org = ORG_1
    repository_mock.add_organization.return_value = ModelOrganization(**ORG_1)

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.put("/organizations/", json=ORG_TO_CREATE)
        actual_org = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_org == expected_org
