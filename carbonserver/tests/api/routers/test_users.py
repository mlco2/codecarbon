from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationsRepository,
)
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectsRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UsersRepository,
)
from carbonserver.api.routers import users
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    Project,
    ProjectCreate,
    User,
    UserCreate,
)

API_KEY = "U5W0EUP9y6bBENOnZWJS0g"

USER_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
USER_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

USER_1 = {
    "id": USER_ID_1,
    "name": "Gontran Bonheur",
    "email": "xyz@email.com",
    "api_key": API_KEY,
    "organizations": [],
    "is_active": True,
}

USER_2 = {
    "id": USER_ID_2,
    "name": "Jonnhy Monnay",
    "email": "1234+1@email.fr",
    "api_key": API_KEY,
    "organizations": [],
    "is_active": True,
}

USER_TO_CREATE = {
    "name": "Gontran Bonheur",
    "email": "xyz@email.com",
    "password": "pwd",
}

USER_WITH_BAD_EMAIL = {
    "name": "Gontran Bonheur",
    "email": "xyz",
    "password": "pwd",
}

###
#  Only needed for the steps after the creation of a user
###
PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
ORGANIZATION_ID = "c13e851f-5c2f-403d-98d0-51fe15df3bc3"

PROJECT_1 = {
    "id": PROJECT_ID,
    "name": "Gontran Bonheur",
    "description": "Default project",
    "organization_id": ORGANIZATION_ID,
    "experiments": [],
}

ORG_1 = {
    "id": ORGANIZATION_ID,
    "api_key": API_KEY,
    "name": "Gontran Bonheur",
    "description": "Default organization",
}
###


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[users])
    app = FastAPI()
    app.container = container
    app.include_router(users.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_create_user(client, custom_test_server):
    repository_mock = mock.Mock(spec=UsersRepository)
    expected_user = USER_1
    repository_mock.create_user.return_value = User(**expected_user)
    project_repository_mock = mock.Mock(spec=ProjectsRepository)
    expected_project = PROJECT_1
    project_repository_mock.add_project.return_value = Project(**expected_project)
    organization_repository_mock = mock.Mock(spec=OrganizationsRepository)
    expected_organization = ORG_1
    organization_repository_mock.add_organization.return_value = Organization(
        **expected_organization
    )

    with custom_test_server.container.user_repository.override(
        repository_mock
    ) and custom_test_server.container.project_repository.override(
        project_repository_mock
    ) and custom_test_server.container.organization_repository.override(
        organization_repository_mock
    ):
        response = client.post("/users", json=USER_TO_CREATE)
        actual_user = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_user == expected_user

    # Check that the mocks have been called
    repository_mock.create_user.assert_called_once()
    project_repository_mock.add_project.assert_called_once()
    organization_repository_mock.add_organization.assert_called_once()
    # Check that the mocks have been called with the correct arguments
    repository_mock.create_user.assert_called_with(UserCreate(**USER_TO_CREATE))
    project_repository_mock.add_project.assert_called_with(ProjectCreate(**PROJECT_1))
    organization_repository_mock.add_organization.assert_called_with(
        OrganizationCreate(**ORG_1)
    )


def test_create_user_with_bad_email_fails_at_http_layer(client):
    response = client.post("/users", json=USER_WITH_BAD_EMAIL)
    actual_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert actual_response["detail"][0]["type"] == "value_error.email"


def test_list_users_list_all_existing_users_with_200(client, custom_test_server):
    repository_mock = mock.Mock(spec=UsersRepository)
    expected_user = USER_1
    expected_user_2 = USER_2
    expected_user_list = [expected_user, expected_user_2]
    repository_mock.list_users.return_value = [
        User(**expected_user),
        User(**expected_user_2),
    ]

    with custom_test_server.container.user_repository.override(repository_mock):
        response = client.get("/users")
        actual_user_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_user_list == expected_user_list


def test_get_user_by_id_returns_correct_user_with_correct_id(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=UsersRepository)
    expected_user = USER_1
    repository_mock.get_user_by_id.return_value = User(**expected_user)

    container_mock = mock.Mock(spec=ServerContainer)
    container_mock.db.return_value = True
    with custom_test_server.container.user_repository.override(repository_mock):
        response = client.get("/users/get_user_by_id/", params={"user_id": USER_ID_1})
        actual_user = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_user == expected_user
