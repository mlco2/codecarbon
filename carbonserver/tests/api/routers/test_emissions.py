from unittest import mock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination
from starlette import status

from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository as EmissionRepository,
)
from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository as ProjectTokenRepository,
)
from carbonserver.api.routers import emissions
from carbonserver.api.schemas import AccessLevel, Emission, ProjectToken
from carbonserver.container import ServerContainer

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
    "wue": 0,
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
    "wue": 0,
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
    "wue": 0,
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
    "wue": 0,
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
    # Prepare the test
    repository_mock = mock.Mock(spec=EmissionRepository)
    expected_emission = EMISSION_ID
    repository_mock.add_emission.return_value = UUID(EMISSION_ID)
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
    project_tokens_repository_mock.get_project_token_by_run_id_and_token.return_value = (
        PROJECT_TOKEN
    )
    # Call the endpoint

    with custom_test_server.container.emission_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/emissions", json=EMISSION_TO_CREATE, headers={"x-api-token": "token"}
        )
        actual_emission = response.json()

    # Asserts
    assert response.status_code == status.HTTP_201_CREATED
    assert actual_emission == expected_emission
    project_tokens_repository_mock.get_project_token_by_run_id_and_token.assert_called_once_with(
        UUID(RUN_1_ID), "token"
    )
    # Call the endpoint without token

    with custom_test_server.container.emission_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response_no_token = client.post("/emissions", json=EMISSION_TO_CREATE)
        response_no_token_message = response_no_token.json()

    # Asserts
    assert response_no_token.status_code == status.HTTP_403_FORBIDDEN
    assert response_no_token_message == {
        "detail": "Not allowed to perform this action. Missing project token"
    }
    project_tokens_repository_mock.get_project_token_by_run_id_and_token.assert_called_once_with(
        UUID(RUN_1_ID), "token"
    )


def test_get_emissions_by_id_returns_correct_emission(client, custom_test_server):
    repository_mock = mock.Mock(spec=EmissionRepository)
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
    repository_mock = mock.Mock(spec=EmissionRepository)
    expected_emissions_id_list = [EMISSION_ID, EMISSION_ID_2]
    repository_mock.get_emissions_from_run.return_value = [
        Emission(**EMISSION_1),
        Emission(**EMISSION_2),
    ]

    with custom_test_server.container.emission_repository.override(repository_mock):
        response = client.get(f"/runs/{RUN_1_ID}/emissions")
        actual_emission_list = response.json()["items"]
        actual_emission_ids_list = [emission["id"] for emission in actual_emission_list]
        diff = set(actual_emission_ids_list) ^ set(expected_emissions_id_list)

    assert not diff
    assert len(actual_emission_ids_list) == len(set(actual_emission_ids_list))
    assert EMISSION_3["id"] not in actual_emission_ids_list


def test_add_emission_with_default_wue_value(client, custom_test_server):
    """Test that WUE defaults to 0 when not provided"""
    # Prepare the test - create emission without WUE field
    emission_without_wue = {
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
        # Note: wue is not provided, should default to 0
    }

    repository_mock = mock.Mock(spec=EmissionRepository)
    repository_mock.add_emission.return_value = UUID(EMISSION_ID)

    # Setup the project token repository
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
    project_tokens_repository_mock.get_project_token_by_run_id_and_token.return_value = (
        PROJECT_TOKEN
    )

    # Call the endpoint
    with custom_test_server.container.emission_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/emissions", json=emission_without_wue, headers={"x-api-token": "token"}
        )

    # Asserts
    assert response.status_code == status.HTTP_201_CREATED

    # Verify that the repository was called with WUE defaulting to 0
    called_emission = repository_mock.add_emission.call_args[0][0]
    assert called_emission.wue == 0, "WUE should default to 0 when not provided"


def test_add_emission_with_custom_wue_value(client, custom_test_server):
    """Test that custom WUE value is properly saved"""
    # Prepare the test - create emission with custom WUE value
    emission_with_wue = {
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
        "wue": 1.5,
    }

    repository_mock = mock.Mock(spec=EmissionRepository)
    repository_mock.add_emission.return_value = UUID(EMISSION_ID)

    # Setup the project token repository
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
    project_tokens_repository_mock.get_project_token_by_run_id_and_token.return_value = (
        PROJECT_TOKEN
    )

    # Call the endpoint
    with custom_test_server.container.emission_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/emissions", json=emission_with_wue, headers={"x-api-token": "token"}
        )

    # Asserts
    assert response.status_code == status.HTTP_201_CREATED

    # Verify that the repository was called with the correct WUE value
    called_emission = repository_mock.add_emission.call_args[0][0]
    assert called_emission.wue == 1.5, "WUE should be set to the provided value"
