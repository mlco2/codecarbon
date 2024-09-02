from unittest import mock

import pytest
from api.mocks import FakeAuthContext, FakeUserWithAuthDependency
from container import ServerContainer
from dependency_injector import providers
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import organizations
from carbonserver.api.routers.authenticate import UserWithAuthDependency
from carbonserver.api.schemas import Organization, OrganizationUser

USER_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

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

ORG_USER = {
    "id": USER_ID_1,
    "name": "user1",
    "email": "user1@local.com",
    "is_active": True,
    "organization_id": ORG_1["id"],
    "is_admin": True,
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[organizations])
    app = FastAPI()
    app.container = container
    app.include_router(organizations.router)
    app.dependency_overrides[UserWithAuthDependency] = FakeUserWithAuthDependency
    app.container.auth_context.override(providers.Factory(FakeAuthContext))

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


def test_patch_organization(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_org = ORG_1
    repository_mock.patch_organization.return_value = Organization(**ORG_1)

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.patch(f"/organizations/{ORG_ID_1}", json={"name": "New Name"})
        actual_org = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_org == expected_org


def test_fetch_org_users(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_user_list = [
        {
            "email": "user1@local.com",
            "id": USER_ID_1,
            "name": "user1",
            "organizations": None,
            "is_active": True,
            "is_admin": True,
        }
    ]
    repository_mock.list_users.return_value = [OrganizationUser(**ORG_USER)]

    with custom_test_server.container.organization_repository.override(repository_mock):
        response = client.get(f"/organizations/{ORG_1['id']}/users")
        actual_user_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_user_list == expected_user_list
