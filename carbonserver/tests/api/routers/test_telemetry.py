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


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    telemetry._recent_requests.clear()
    yield
    telemetry._recent_requests.clear()


@pytest.fixture
def repository_mock(custom_test_server):
    repository_mock = mock.Mock(spec=TelemetryRepository)
    repository_mock.add_telemetry.return_value = UUID(TELEMETRY_ID)
    with custom_test_server.container.telemetry_repository.override(repository_mock):
        yield repository_mock


def test_add_telemetry_needs_no_token(client, repository_mock):
    response = client.post("/telemetry", json=MINIMAL_TELEMETRY_TO_CREATE)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == TELEMETRY_ID
    repository_mock.add_telemetry.assert_called_once()


def test_unknown_fields_are_rejected(client, repository_mock):
    response = client.post(
        "/telemetry",
        json={**MINIMAL_TELEMETRY_TO_CREATE, "total_emissions_kg": 0.42},
    )

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()


def test_disabled_telemetry_is_rejected(client, repository_mock):
    response = client.post(
        "/telemetry",
        json={**MINIMAL_TELEMETRY_TO_CREATE, "telemetry_level": "disabled"},
    )

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()


def test_coordinates_are_rejected(client, repository_mock):
    response = client.post(
        "/telemetry",
        json={**MINIMAL_TELEMETRY_TO_CREATE, "latitude": 48.8, "longitude": 2.3},
    )

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()


def test_oversized_string_is_rejected(client, repository_mock):
    response = client.post(
        "/telemetry",
        json={**MINIMAL_TELEMETRY_TO_CREATE, "cpu_model": "x" * 257},
    )

    assert response.status_code == 422
    repository_mock.add_telemetry.assert_not_called()


def test_rate_limit_returns_429_per_ip(client, repository_mock, monkeypatch):
    monkeypatch.setattr(telemetry, "RATE_LIMIT", 2)

    codes = [
        client.post("/telemetry", json=MINIMAL_TELEMETRY_TO_CREATE).status_code
        for _ in range(3)
    ]

    assert codes == [201, 201, 429]
    assert repository_mock.add_telemetry.call_count == 2
    # Another IP has its own budget.
    other = TestClient(client.app, client=("10.0.0.2", 50000))
    assert other.post("/telemetry", json=MINIMAL_TELEMETRY_TO_CREATE).status_code == 201


def test_rate_limit_window_expires(monkeypatch):
    monkeypatch.setattr(telemetry, "RATE_LIMIT", 1)
    now = [1000.0]
    monkeypatch.setattr(telemetry.time, "monotonic", lambda: now[0])

    assert telemetry._rate_limited("1.2.3.4") is False
    assert telemetry._rate_limited("1.2.3.4") is True
    now[0] += telemetry.RATE_WINDOW_SECONDS + 1
    assert telemetry._rate_limited("1.2.3.4") is False


def test_rate_limited_is_atomic_under_concurrency(monkeypatch):
    """FastAPI runs sync endpoints in a threadpool; _rate_limited must not
    let concurrent callers both slip past the limit check (see the lock in
    carbonserver/carbonserver/api/routers/telemetry.py)."""
    import threading

    monkeypatch.setattr(telemetry, "RATE_LIMIT", 5)
    admitted = []
    admitted_lock = threading.Lock()
    barrier = threading.Barrier(20)

    def call():
        barrier.wait()
        limited = telemetry._rate_limited("9.9.9.9")
        if not limited:
            with admitted_lock:
                admitted.append(1)

    threads = [threading.Thread(target=call) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(admitted) == telemetry.RATE_LIMIT


def test_rate_limit_memory_is_bounded(monkeypatch):
    monkeypatch.setattr(telemetry, "MAX_TRACKED_IPS", 2)

    for host in ("1.1.1.1", "2.2.2.2", "3.3.3.3"):
        telemetry._rate_limited(host)

    assert list(telemetry._recent_requests) == ["3.3.3.3"]
