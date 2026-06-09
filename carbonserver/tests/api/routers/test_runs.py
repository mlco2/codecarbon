from unittest import mock
from uuid import UUID

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository as ProjectTokenRepository,
)
from carbonserver.api.infra.repositories.repository_runs import (
    SqlAlchemyRepository as RunRepository,
)
from carbonserver.api.routers import runs
from carbonserver.api.schemas import AccessLevel, ProjectToken, Run
from carbonserver.container import ServerContainer

EXPE_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EXPE_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

RUN_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
RUN_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

RUN_TO_CREATE = {
    "timestamp": "2021-06-22 14:15:15",
    "experiment_id": EXPE_ID,
    "os": "macOS-10.15.7-x86_64-i386-64bit",
    "python_version": "3.8.0",
    "codecarbon_version": "2.1.3",
    "cpu_count": 12,
    "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
    "gpu_count": 4,
    "gpu_model": "NVIDIA",
    "longitude": -7.6174,
    "latitude": 33.5822,
    "region": "EUROPE",
    "provider": "AWS",
    "ram_total_size": 83948.22,
    "tracking_mode": "Machine",
}

RUN_1 = {
    "id": RUN_ID,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "experiment_id": EXPE_ID,
    "os": "macOS-10.15.7-x86_64-i386-64bit",
    "python_version": "3.8.0",
    "codecarbon_version": "2.1.3",
    "cpu_count": 12,
    "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
    "gpu_count": 4,
    "gpu_model": "NVIDIA",
    "longitude": -7.6174,
    "latitude": 33.5822,
    "region": "EUROPE",
    "provider": "AWS",
    "ram_total_size": 83948.22,
    "tracking_mode": "Machine",
}


RUN_2 = {
    "id": RUN_ID_2,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "experiment_id": EXPE_ID_2,
    "os": "macOS-10.15.7-x86_64-i386-64bit",
    "python_version": "3.8.0",
    "codecarbon_version": "2.1.3",
    "cpu_count": 12,
    "cpu_model": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
    "gpu_count": 4,
    "gpu_model": "NVIDIA",
    "longitude": -7.6174,
    "latitude": 33.5822,
    "region": "EUROPE",
    "provider": "AWS",
    "ram_total_size": 83948.22,
    "tracking_mode": "Machine",
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[runs])
    app = FastAPI()
    app.container = container
    app.include_router(runs.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_run(client, custom_test_server):
    # Prepare the test
    repository_mock = mock.Mock(spec=RunRepository)
    expected_run = RUN_1
    repository_mock.add_run.return_value = Run(**RUN_1)

    # Setup the project token repository (used to check the auth token)
    project_tokens_repository_mock = mock.Mock(spec=ProjectTokenRepository)
    PROJECT_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")
    PROJECT_TOKEN_ID = UUID("e60afb92-17b7-4720-91a0-1ae91e409ba7")
    PROJECT_TOKEN = ProjectToken(
        id=PROJECT_TOKEN_ID,
        project_id=PROJECT_ID,
        name="Project",
        token="token",
        access=AccessLevel.WRITE.value,
    )
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.return_value = (
        PROJECT_TOKEN
    )
    # Call the endpoint

    with custom_test_server.container.run_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/runs", json=RUN_TO_CREATE, headers={"x-api-token": "token"}
        )
        actual_run = response.json()

    # Asserts
    assert response.status_code == status.HTTP_201_CREATED
    assert actual_run == expected_run
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.assert_called_once_with(
        UUID(EXPE_ID), "token"
    )

    # Call the endpoint without token

    with custom_test_server.container.run_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response_no_token = client.post("/runs", json=RUN_TO_CREATE)
        response_no_token_message = response_no_token.json()

    # Asserts
    assert response_no_token.status_code == status.HTTP_403_FORBIDDEN
    assert response_no_token_message == {
        "detail": "Not allowed to perform this action. Missing project token"
    }
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.assert_called_once_with(
        UUID(EXPE_ID), "token"
    )


def test_get_run_by_id_returns_correct_run(client, custom_test_server):
    repository_mock = mock.Mock(spec=RunRepository)
    expected_run = RUN_1
    repository_mock.get_one_run.return_value = Run(**expected_run)

    with custom_test_server.container.run_repository.override(repository_mock):
        response = client.get("/runs/read_run/", params={"id": RUN_ID})
        actual_run = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_run == expected_run


def test_list_runs_returns_all_runs(client, custom_test_server):
    repository_mock = mock.Mock(spec=RunRepository)
    expected_run_1 = RUN_1
    expected_run_2 = RUN_2
    expected_org_list = [expected_run_1, expected_run_2]
    repository_mock.list_runs.return_value = [
        Run(**expected_run_1),
        Run(**expected_run_2),
    ]

    with custom_test_server.container.run_repository.override(repository_mock):
        response = client.get("/runs")
        actual_org_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_org_list == expected_org_list


def test_get_runs_from_experiment_returns_correct_run(client, custom_test_server):
    repository_mock = mock.Mock(spec=RunRepository)
    expected_run_1 = RUN_1
    expected_run_list = [RUN_1]
    repository_mock.get_runs_from_experiment.return_value = [
        Run(**expected_run_1),
    ]

    with custom_test_server.container.run_repository.override(repository_mock):
        response = client.get(f"/experiments/{EXPE_ID}/runs")
        actual_run_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_run_list == expected_run_list
