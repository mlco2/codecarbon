from unittest import mock
from uuid import UUID

import pytest
from container import ServerContainer
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination
from starlette import status

from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import emissions
from carbonserver.api.schemas import Emission

RUN_1_ID = "40088f1a-d28e-4980-8d80-bf5600056a14"
RUN_2_ID = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

EMISSION_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EMISSION_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
EMISSION_ID_3 = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

EMISSION_TO_CREATE = {
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
    "duration": 98745,
    "emissions_sum": 206.548444,
    "emissions_rate": 89.548444,
    "cpu_power": 0.3,
    "gpu_power": 0.0,
    "ram_power": 0.15,
    "cpu_energy": 55.21874,
    "gpu_energy": 0.0,
    "ram_energy": 2.0,
    "energy_consumed": 57.21874,
}

EMISSION_1 = {
    "id": EMISSION_ID,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": RUN_1_ID,
    "duration": 98745,
    "emissions_sum": 106.548444,
    "emissions_rate": 0.548444,
    "cpu_power": 0.3,
    "gpu_power": 0.0,
    "ram_power": 0.15,
    "cpu_energy": 55.21874,
    "gpu_energy": 0.0,
    "ram_energy": 2.0,
    "energy_consumed": 57.21874,
}

EMISSION_2 = {
    "id": EMISSION_ID_2,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": RUN_1_ID,
    "duration": 98745,
    "emissions_sum": 136.548444,
    "emissions_rate": 5.548444,
    "cpu_power": 0.3,
    "gpu_power": 0.0,
    "ram_power": 0.15,
    "cpu_energy": 55.21874,
    "gpu_energy": 0.0,
    "ram_energy": 2.0,
    "energy_consumed": 57.21874,
}


EMISSION_3 = {
    "id": EMISSION_ID_3,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": RUN_2_ID,
    "duration": 98745,
    "emissions_sum": 256.548444,
    "emissions_rate": 98.548444,
    "cpu_power": 0.3,
    "gpu_power": 0.0,
    "ram_power": 0.15,
    "cpu_energy": 55.21874,
    "gpu_energy": 0.0,
    "ram_energy": 2.0,
    "energy_consumed": 57.21874,
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[emissions])
    app = FastAPI()
    app.container = container
    app.include_router(emissions.router)
    add_pagination(app)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_emission(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_emission = EMISSION_ID
    repository_mock.add_emission.return_value = UUID(EMISSION_ID)

    with custom_test_server.container.emission_repository.override(repository_mock):
        response = client.post("/emissions", json=EMISSION_TO_CREATE)
        actual_emission = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_emission == expected_emission


def test_get_emissions_by_id_returns_correct_emission(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_emission = EMISSION_1
    repository_mock.get_one_emission.return_value = Emission(**expected_emission)

    with custom_test_server.container.emission_repository.override(repository_mock):
        response = client.get(
            "/emissions/read_emission/", params={"emission_id": EMISSION_ID}
        )
        actual_emission = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_emission == expected_emission


def test_get_emissions_from_run_retreives_all_emissions_from_run(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_emissions_id_list = [EMISSION_ID, EMISSION_ID_2]
    repository_mock.get_emissions_from_run.return_value = [
        Emission(**EMISSION_1),
        Emission(**EMISSION_2),
    ]

    with custom_test_server.container.emission_repository.override(repository_mock):
        response = client.get(
            "/emissions/run/get_emissions_from_run/", params={"run_id": RUN_1_ID}
        )
        actual_emission_list = response.json()["items"]
        actual_emission_ids_list = [emission["id"] for emission in actual_emission_list]
        diff = set(actual_emission_ids_list) ^ set(expected_emissions_id_list)

    assert not diff
    assert len(actual_emission_ids_list) == len(set(actual_emission_ids_list))
    assert EMISSION_3["id"] not in actual_emission_ids_list
