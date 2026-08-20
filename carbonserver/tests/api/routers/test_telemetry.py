from unittest import mock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status

from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository as ProjectTokenRepository,
)
from carbonserver.api.infra.repositories.repository_telemetry import (
    SqlAlchemyRepository as TelemetryRepository,
)
from carbonserver.api.routers import telemetry
from carbonserver.api.schemas import AccessLevel, ProjectToken
from carbonserver.config import settings
from carbonserver.container import ServerContainer

TELEMETRY_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

MINIMAL_TELEMETRY_TO_CREATE = {
    "timestamp": "2026-05-03T12:00:00+00:00",
    "telemetry_level": "minimal",
    "os": "Linux-5.10.0-x86_64",
    "country_name": "France",
    "country_iso_code": "FRA",
    "cpu_count": 12,
    "python_version": "3.11.5",
    "codecarbon_version": "3.2.6",
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[telemetry])
    app = FastAPI()
    app.container = container
    app.include_router(telemetry.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_telemetry(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    repository_mock.add_telemetry.return_value = UUID(TELEMETRY_ID)
    project_tokens_repository_mock = mock.Mock(spec=ProjectTokenRepository)
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.return_value = ProjectToken(
        id=UUID("e60afb92-17b7-4720-91a0-1ae91e409ba7"),
        project_id=UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d"),
        name="Telemetry",
        token="token",
        access=AccessLevel.WRITE.value,
    )

    with custom_test_server.container.telemetry_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/telemetry",
            json=MINIMAL_TELEMETRY_TO_CREATE,
            headers={"x-api-token": "token"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == TELEMETRY_ID
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.assert_called_once_with(
        settings.telemetry_experiment_id, "token"
    )


def test_add_telemetry_rejects_missing_token(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    project_tokens_repository_mock = mock.Mock(spec=ProjectTokenRepository)

    with custom_test_server.container.telemetry_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post("/telemetry", json=MINIMAL_TELEMETRY_TO_CREATE)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Not allowed to perform this action. Missing project token"
    }
    repository_mock.add_telemetry.assert_not_called()
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.assert_not_called()


def test_minimal_telemetry_rejects_extensive_fields(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    project_tokens_repository_mock = mock.Mock(spec=ProjectTokenRepository)
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.return_value = ProjectToken(
        id=UUID("e60afb92-17b7-4720-91a0-1ae91e409ba7"),
        project_id=UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d"),
        name="Telemetry",
        token="token",
        access=AccessLevel.WRITE.value,
    )
    telemetry_with_extensive_field = {
        **MINIMAL_TELEMETRY_TO_CREATE,
        "total_emissions_kg": 0.42,
    }

    with custom_test_server.container.telemetry_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/telemetry",
            json=telemetry_with_extensive_field,
            headers={"x-api-token": "token"},
        )

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()


def test_disabled_telemetry_is_rejected(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    project_tokens_repository_mock = mock.Mock(spec=ProjectTokenRepository)
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.return_value = ProjectToken(
        id=UUID("e60afb92-17b7-4720-91a0-1ae91e409ba7"),
        project_id=UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d"),
        name="Telemetry",
        token="token",
        access=AccessLevel.WRITE.value,
    )
    disabled_telemetry = {
        **MINIMAL_TELEMETRY_TO_CREATE,
        "telemetry_level": "disabled",
    }

    with custom_test_server.container.telemetry_repository.override(
        repository_mock
    ) and custom_test_server.container.project_token_repository.override(
        project_tokens_repository_mock
    ):
        response = client.post(
            "/telemetry",
            json=disabled_telemetry,
            headers={"x-api-token": "token"},
        )

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()
