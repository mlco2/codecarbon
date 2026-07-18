"""Verify carbonserver uses the shared telemetry token defaults."""

from pathlib import Path
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
from carbonserver.telemetry_defaults import (
    DEFAULT_TELEMETRY_API_KEY,
    DEFAULT_TELEMETRY_EXPERIMENT_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TELEMETRY_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")

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


def test_shared_defaults_are_symlinked():
    client_defaults_path = REPO_ROOT / "codecarbon" / "core" / "telemetry" / "defaults.py"
    server_defaults_path = REPO_ROOT / "carbonserver" / "carbonserver" / "telemetry_defaults.py"
    shared_defaults_path = REPO_ROOT / "shared" / "telemetry_defaults.py"

    assert client_defaults_path.is_symlink()
    assert server_defaults_path.is_symlink()
    assert client_defaults_path.resolve() == shared_defaults_path.resolve()
    assert server_defaults_path.resolve() == shared_defaults_path.resolve()
    assert settings.telemetry_experiment_id == DEFAULT_TELEMETRY_EXPERIMENT_ID


def test_add_telemetry_accepts_shared_default_token(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    repository_mock.add_telemetry.return_value = TELEMETRY_ID
    project_tokens_repository_mock = mock.Mock(spec=ProjectTokenRepository)
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.return_value = ProjectToken(
        id=UUID("e60afb92-17b7-4720-91a0-1ae91e409ba7"),
        project_id=UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d"),
        name="Telemetry",
        token=DEFAULT_TELEMETRY_API_KEY,
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
            headers={"x-api-token": DEFAULT_TELEMETRY_API_KEY},
        )

    assert response.status_code == status.HTTP_201_CREATED
    project_tokens_repository_mock.get_project_token_by_experiment_id_and_token.assert_called_once_with(
        DEFAULT_TELEMETRY_EXPERIMENT_ID,
        DEFAULT_TELEMETRY_API_KEY,
    )
    saved_telemetry = repository_mock.add_telemetry.call_args.args[0]
    assert saved_telemetry.os == MINIMAL_TELEMETRY_TO_CREATE["os"]
    assert saved_telemetry.country_name == MINIMAL_TELEMETRY_TO_CREATE["country_name"]
