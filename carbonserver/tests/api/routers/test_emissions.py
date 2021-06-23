from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status

from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import emissions

RUN_1_ID = "40088f1a-d28e-4980-8d80-bf5600056a14"
RUN_2_ID = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

EMISSION_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
EMISSION_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
EMISSION_ID_3 = "07614c15-c5b0-4c9a-8101-6b6ad3733543"

EMISSION_TO_CREATE = {
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
    "duration": 98745,
    "emissions": 1.548444,
    "energy_consumed": 57.21874,
}

EMISSION_1 = {
    "id": EMISSION_ID,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": RUN_1_ID,
    "duration": 98745,
    "emissions": 1.548444,
    "energy_consumed": 57.21874,
}

EMISSION_2 = {
    "id": EMISSION_ID_2,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": RUN_1_ID,
    "duration": 98745,
    "emissions": 1.548444,
    "energy_consumed": 57.21874,
}


EMISSION_3 = {
    "id": EMISSION_ID_3,
    "timestamp": "2021-04-04T08:43:00+02:00",
    "run_id": RUN_2_ID,
    "duration": 98745,
    "emissions": 1.548444,
    "energy_consumed": 57.21874,
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[emissions])
    app = FastAPI()
    app.container = container
    app.include_router(emissions.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_emission(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_emission = EMISSION_1
    repository_mock.add_emission.return_value = SqlModelEmission(**EMISSION_1)

    with custom_test_server.container.emission_repository.override(repository_mock):
        response = client.put("/emissions/", json=EMISSION_TO_CREATE)
        actual_emission = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_emission == expected_emission


def test_get_emissions_by_id_returns_correct_emission(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_emission = EMISSION_1
    repository_mock.get_one_emission.return_value = SqlModelEmission(
        **expected_emission
    )

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
        SqlModelEmission(**EMISSION_1),
        SqlModelEmission(**EMISSION_2),
    ]

    with custom_test_server.container.emission_repository.override(repository_mock):
        response = client.get(
            "/emissions/run/get_emissions_from_run/", params={"run_id": RUN_1_ID}
        )
        actual_emission_list = response.json()
        actual_emission_ids_list = [emission["id"] for emission in actual_emission_list]
        diff = set(actual_emission_ids_list) ^ set(expected_emissions_id_list)

    assert not diff
    assert len(actual_emission_ids_list) == len(set(actual_emission_ids_list))
    assert EMISSION_3["id"] not in actual_emission_ids_list
