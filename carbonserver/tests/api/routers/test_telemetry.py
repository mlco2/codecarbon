from unittest import mock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status

from carbonserver.api.infra.repositories.repository_telemetry import (
    SqlAlchemyRepository as TelemetryRepository,
)
from carbonserver.api.routers import telemetry
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

    with custom_test_server.container.telemetry_repository.override(repository_mock):
        response = client.post("/telemetry", json=MINIMAL_TELEMETRY_TO_CREATE)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == TELEMETRY_ID


def test_minimal_telemetry_rejects_extensive_fields(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    telemetry_with_extensive_field = {
        **MINIMAL_TELEMETRY_TO_CREATE,
        "torch_version": "2.2.0",
    }

    with custom_test_server.container.telemetry_repository.override(repository_mock):
        response = client.post("/telemetry", json=telemetry_with_extensive_field)

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()


def test_disabled_telemetry_is_rejected(client, custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    disabled_telemetry = {
        **MINIMAL_TELEMETRY_TO_CREATE,
        "telemetry_level": "disabled",
    }

    with custom_test_server.container.telemetry_repository.override(repository_mock):
        response = client.post("/telemetry", json=disabled_telemetry)

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()
