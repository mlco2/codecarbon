from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import organizations
from carbonserver.api.routers.authenticate import UserWithAuthDependency
from carbonserver.api.schemas import Organization, User

USER_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"


class FakeUserWithAuthDependency:
    db_user = User(id=USER_ID_1, name="user1", email="user1@local.com", is_active=True)
    auth_user = {"sub": USER_ID_1}


ORG_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
ORG_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_TO_CREATE = {
    "name": "Data For Good",
    "description": "DFG Organization",
}

ORG_1 = {
    "id": ORG_ID_1,
    "name": "Data For Good",
    "description": "DFG Organization",
}

ORG_2 = {
    "id": ORG_ID_2,
    "name": "Code Carbon",
    "description": "Code Carbon Organization",
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


@pytest.mark.skip(reason="test server with no auth in dev")
def test_add_org(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org = ORG_1
    repository_mock.add_organization.return_value = Organization(**ORG_1)

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.post("/organizations", json=ORG_TO_CREATE)
        actual_org = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_org == expected_org


@pytest.mark.skip(reason="test server with no auth in dev")
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


def test_list_organizations_returns_all_orgs_for_user(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org_1 = ORG_1
    expected_org_2 = ORG_2
    expected_org_list = [expected_org_1, expected_org_2]
    repository_mock.list_organizations.return_value = [
        Organization(**expected_org_1),
        Organization(**expected_org_2),
    ]
    custom_test_server.dependency_overrides[UserWithAuthDependency] = (
        FakeUserWithAuthDependency
    )
    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.get("/organizations")
        actual_org_list = response.json()
    repository_mock.list_organizations.assert_called_with(
        user=FakeUserWithAuthDependency.db_user
    )

    assert response.status_code == status.HTTP_200_OK
    assert actual_org_list == expected_org_list


@pytest.mark.skip(reason="test server with no auth in dev")
def test_patch_organization(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org = ORG_1
    repository_mock.patch_organization.return_value = Organization(**ORG_1)

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.patch(f"/organizations/{ORG_ID_1}", json={"name": "New Name"})
        actual_org = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_org == expected_org
