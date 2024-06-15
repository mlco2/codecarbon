from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_projects import SqlAlchemyRepository
from carbonserver.api.routers import projects
from carbonserver.api.schemas import Project

PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
PROJECT_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"


PROJECT_TO_CREATE = {
    "name": "API Code Carbon",
    "description": "API for Code Carbon",
}

PROJECT_1 = {
    "id": PROJECT_ID,
    "name": "API Code Carbon",
    "description": "API for Code Carbon",
    "experiments": [],
}


PROJECT_2 = {
    "id": PROJECT_ID_2,
    "name": "API Code Carbon",
    "description": "Calculates CO2 emissions of AI projects",
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[projects])
    app = FastAPI()
    app.container = container
    app.include_router(projects.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_project(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    repository_mock.add_project.return_value = Project(**PROJECT_1)

    with custom_test_server.container.project_repository.override(repository_mock):
        response = client.post("/project", json=PROJECT_TO_CREATE)
        actual_project = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_project == expected_project


def test_get_project_by_id_returns_correct_project(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT_1
    repository_mock.get_one_project.return_value = Project(**expected_project)

    with custom_test_server.container.project_repository.override(repository_mock):
        response = client.get("/project/read_project/", params={"id": PROJECT_ID})
        actual_project = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_project == expected_project
