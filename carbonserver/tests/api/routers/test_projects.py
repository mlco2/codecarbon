from unittest import mock

import pytest
from api.mocks import FakeAuthContext, FakeUserWithAuthDependency
from container import ServerContainer
from dependency_injector import providers
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_projects import SqlAlchemyRepository
from carbonserver.api.routers import projects
from carbonserver.api.schemas import Project
from carbonserver.api.services.auth_service import MandatoryUserWithAuthDependency


@pytest.fixture
def custom_test_server() -> FastAPI:
    container = ServerContainer()
    container.wire(modules=[projects])

    app = FastAPI()
    app.container = container
    app.include_router(projects.router)
    app.dependency_overrides[MandatoryUserWithAuthDependency] = (
        FakeUserWithAuthDependency
    )
    app.container.auth_context.override(providers.Factory(FakeAuthContext))
    yield app


@pytest.fixture
def custom_test_server_with_auth() -> FastAPI:
    container = ServerContainer()
    container.wire(modules=[projects])

    app = FastAPI()
    app.container = container
    app.include_router(projects.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


@pytest.fixture
def client_with_auth(custom_test_server_with_auth):
    yield TestClient(custom_test_server_with_auth)


PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
PROJECT_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
PROJECT_ID_3 = "df1ebed2-ee06-4d2f-9da4-27676e3a9bf3"

ORGANIZATION_ID = "c13e851f-5c2f-403d-98d0-51fe15df3bc3"
ORGANIZATION_ID_2 = "c13e851f-5c2f-403d-98d0-51fe15df3bc4"

PROJECT_TO_CREATE = {
    "name": "API Code Carbon",
    "description": "API for Code Carbon",
    "organization_id": ORGANIZATION_ID,
}
PROJECT_PATCH = {
    "name": "API Code Carbon",
    "description": "API for Code Carbon",
}

PROJECT_1 = {
    "id": PROJECT_ID,
    "name": "API Code Carbon",
    "description": "API for Code Carbon",
    "organization_id": ORGANIZATION_ID,
    "experiments": [],
    "public": False,
}

PROJECT_2 = {
    "id": PROJECT_ID_2,
    "name": "API Code Carbon",
    "description": "Calculates CO2 emissions of AI projects",
    "organization_id": ORGANIZATION_ID_2,
    "public": False,
}

PROJECT_3 = {
    "id": PROJECT_ID_3,
    "name": "Public project",
    "description": "Public project",
    "organization_id": ORGANIZATION_ID_2,
    "experiments": [],
    "public": True,
}


def test_add_project(client, custom_test_server):
    project_repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    project_repository_mock.add_project.return_value = Project(**PROJECT_1)

    with custom_test_server.container.project_repository.override(
        project_repository_mock
    ):
        response = client.post("/projects", json=PROJECT_TO_CREATE)
        actual_project = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_project == expected_project


def test_delete_project(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.delete_project.return_value = None

    with custom_test_server.container.project_repository.override(repository_mock):
        response = client.delete(f"/projects/{PROJECT_ID}", params={"id": PROJECT_ID})

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_patch_project(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    repository_mock.patch_project.return_value = Project(**expected_project)

    with custom_test_server.container.project_repository.override(repository_mock):
        response = client.patch(f"/projects/{PROJECT_ID}", json=PROJECT_PATCH)
        actual_project = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_project == expected_project


def test_get_project_by_id_returns_correct_project(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    repository_mock.get_one_project.return_value = Project(**expected_project)

    with custom_test_server.container.project_repository.override(repository_mock):
        response = client.get("/projects/read_project/", params={"id": PROJECT_ID})
        actual_project = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_project == expected_project


def test_get_projects_from_organization_returns_correct_project(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    expected_project_list = [expected_project]
    repository_mock.get_projects_from_organization.return_value = [
        Project(**expected_project),
    ]

    with custom_test_server.container.project_repository.override(repository_mock):
        response = client.get(f"/organizations/{ORGANIZATION_ID}/projects")
        actual_project_list = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert actual_project_list == expected_project_list


@pytest.mark.xfail(raises=Exception)
def test_get_private_project_no_auth(client_with_auth, custom_test_server_with_auth):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    repository_mock.get_one_project.return_value = Project(**expected_project)
    repository_mock.is_project_public.return_value = False

    with custom_test_server_with_auth.container.project_repository.override(
        repository_mock
    ):
        client_with_auth.get("/projects/{PROJECT_ID}")


def test_get_public_project_no_auth(client_with_auth, custom_test_server_with_auth):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_3
    repository_mock.get_one_project.return_value = Project(**expected_project)
    repository_mock.is_project_public.return_value = True

    with custom_test_server_with_auth.container.project_repository.override(
        repository_mock
    ):
        response = client_with_auth.get("/projects/{PROJECT_ID}")
        actual_project = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_project == expected_project
