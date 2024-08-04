from datetime import datetime
from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette import status
from starlette.testclient import TestClient

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository as ExperimentRepository,
)
from carbonserver.api.routers import experiments
from carbonserver.api.schemas import Experiment

PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

EXPERIMENT_ID = "10276e58-6df7-42cf-abb8-429773a35eb5"
EXPERIMENT_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
EXPERIMENT_ID_3 = "c13e851f-5c2f-403d-98d0-51fe15df3bc3"

EXPERIMENT_GLOBAL_SUM = {
    "id": EXPERIMENT_ID,
    "timestamp": datetime.now().isoformat(),
    "name": "Run on Premise",
    "description": "Premise API for Code Carbon",
    "emission_sum": 1544.54,
    "energy_consumed": 57.21874,
    "duration": 98745,
}

EXPERIMENT_TO_CREATE = {
    "timestamp": "2021-04-04T06:43:00",
    "name": "Run on Premise",
    "description": "Premise API for Code Carbon",
    "country_name": "France",
    "country_iso_code": "FRA",
    "region": "france",
    "on_cloud": True,
    "cloud_provider": "Premise",
    "cloud_region": "Premise",
    "project_id": PROJECT_ID,
}

EXPERIMENT_1 = {
    "id": EXPERIMENT_ID,
    "timestamp": "2021-04-04T06:43:00",
    "name": "Run on Premise",
    "description": "Premise API for Code Carbon",
    "country_name": "France",
    "country_iso_code": "FRA",
    "region": "france",
    "on_cloud": True,
    "cloud_provider": "Premise",
    "cloud_region": "Premise",
    "project_id": PROJECT_ID,
}

EXPERIMENT_2 = {
    "id": EXPERIMENT_ID_2,
    "timestamp": "2021-04-04T06:43:00",
    "name": "Run on AWS",
    "description": "AWS Run for test",
    "country_name": "France",
    "country_iso_code": "FRA",
    "region": "france",
    "on_cloud": True,
    "cloud_provider": "AWS",
    "cloud_region": "eu-west-1",
    "project_id": PROJECT_ID,
}

EXPERIMENT_WITH_DETAILS = {
    "experiment_id": "943b2aa5-9e21-41a9-8a38-562505b4b2aa",
    "timestamp": "2021-10-07T20:19:27.716693",
    "name": "Code Carbon user test",
    "description": "Code Carbon user test with default project",
    "country_name": "France",
    "country_iso_code": "FRA",
    "region": "france",
    "on_cloud": False,
    "cloud_provider": None,
    "cloud_region": None,
    "emission": 152.28955200363455,
    "cpu_power": 5760,
    "gpu_power": 2983.9739999999993,
    "ram_power": 806.0337192959997,
    "cpu_energy": 191.8251863024175,
    "gpu_energy": 140.01098718681496,
    "ram_energy": 26.84332784201141,
    "energy_consumed": 358.6795013312438,
    "duration": 7673204,
    "emissions_rate": 1.0984556074701752,
    "emissions_count": 64,
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[experiments])
    app = FastAPI()
    app.container = container
    app.include_router(experiments.router)
    add_pagination(app)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_experiment(client, custom_test_server):
    repository_mock = mock.Mock(spec=ExperimentRepository)
    expected_expriment = EXPERIMENT_1
    repository_mock.add_experiment.return_value = Experiment(**EXPERIMENT_1)

    with custom_test_server.container.experiment_repository.override(repository_mock):
        response = client.post("/experiments", json=EXPERIMENT_TO_CREATE)
        actual_experiment = response.json()
    print(actual_experiment)
    print(type(actual_experiment))
    assert response.status_code == status.HTTP_201_CREATED
    assert actual_experiment == expected_expriment


def test_get_experiment_by_id_returns_correct_experiment(client, custom_test_server):
    # Prepare the test
    repository_mock = mock.Mock(spec=ExperimentRepository)
    expected_experiment = EXPERIMENT_1
    repository_mock.get_one_experiment.return_value = Experiment(**EXPERIMENT_1)

    # Call the endpoint

    with custom_test_server.container.experiment_repository.override(repository_mock):
        response = client.get(f"/experiments/{EXPERIMENT_ID}")
        actual_experiment = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert actual_experiment == expected_experiment


def test_get_experiment_of_project_retrieves_all_experiments_of_project(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=ExperimentRepository)
    expected_experiments_id_list = [EXPERIMENT_ID, EXPERIMENT_ID_2]
    repository_mock.get_experiments_from_project.return_value = [
        Experiment(**EXPERIMENT_1),
        Experiment(**EXPERIMENT_2),
    ]

    with custom_test_server.container.experiment_repository.override(repository_mock):
        response = client.get(f"/projects/{PROJECT_ID}/experiments")
        actual_experiments_list = response.json()
        actual_experiments_ids_list = [
            experiment["id"] for experiment in actual_experiments_list
        ]
        diff = set(actual_experiments_ids_list) ^ set(expected_experiments_id_list)

    assert not diff
    assert len(actual_experiments_ids_list) == len(set(actual_experiments_ids_list))
    assert EXPERIMENT_ID_3 not in actual_experiments_ids_list
