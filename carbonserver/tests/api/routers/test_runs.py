from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.routers import runs

EXPE_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EXPE_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

RUN_ID = "f52fe339-164d-4c2b-a8c0-f562dfcerun"
RUN_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfcerun"

RUN_TO_CREATE = {
    "timestamp": "2021-06-22 14:15:15",
    "experiment_id": EXPE_ID,
}

RUN_1 = {
    "id": RUN_ID,
    # timestamp
    "experiment_id": EXPE_ID,
}


RUN_2 = {
    "id": RUN_ID_2,
    "experiment_id": EXPE_ID_2,
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
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_run = RUN_1
    repository_mock.add_run.return_value = SqlModelRun(**RUN_1)

    with custom_test_server.container.run_repository.override(repository_mock):
        response = client.put("/run", json=RUN_TO_CREATE)
        actual_run = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_run == expected_run


def test_get_run_by_id_returns_correct_run(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_run = RUN_1
    repository_mock.get_one_run.return_value = [
        SqlModelRun(**expected_run),
    ]

    with custom_test_server.container.run_repository.override(repository_mock):
        response = client.get("/run/read_run/", params={"id": RUN_ID})
        actual_run = response.json()[0]

    assert response.status_code == status.HTTP_200_OK
    assert actual_run == expected_run


def test_list_runs_returns_all_runs(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_run_1 = RUN_1
    expected_run_2 = RUN_2
    expected_org_list = [expected_run_1, expected_run_2]
    repository_mock.list_runs.return_value = [
        SqlModelRun(**expected_run_1),
        SqlModelRun(**expected_run_2),
    ]

    with custom_test_server.container.run_repository.override(repository_mock):
        response = client.get("/runs")
        actual_org_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_org_list == expected_org_list
