from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import organizations
from carbonserver.api.schemas import Organization

API_KEY = "U5W0EUP9y6bBENOnZWJS0g"

ORG_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
ORG_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_TO_CREATE = {
    "name": "Data For Good",
    "description": "DFG Organization",
}

ORG_1 = {
    "id": ORG_ID_1,
    "api_key": API_KEY,
    "name": "Data For Good",
    "description": "DFG Organization",
    "teams": [],
}


ORG_2 = {
    "id": ORG_ID_2,
    "api_key": API_KEY,
    "name": "Code Carbon",
    "description": "Code Carbon Organization",
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
    repository_mock.add_organization.return_value = Organization(**ORG_1)

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.post("/organizations", json=ORG_TO_CREATE)
        actual_org = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_org == expected_org


def test_get_organization_by_id_returns_correct_org(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org = ORG_1
    repository_mock.get_one_organization.return_value = Organization(**expected_org)

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.get(
            "/organizations/read_organization/", params={"organization_id": ORG_ID_1}
        )
        actual_org = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_org == expected_org


def test_list_organizations_returns_all_orgs(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org_1 = ORG_1
    expected_org_2 = ORG_2
    expected_org_list = [expected_org_1, expected_org_2]
    repository_mock.list_organizations.return_value = [
        Organization(**expected_org_1),
        Organization(**expected_org_2),
    ]

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.get("/organizations")
        actual_org_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_org_list == expected_org_list
