import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import codecarbon.integrations.fastapi.middleware as cc_fastapi_middleware
from codecarbon.integrations.fastapi import add_codecarbon_middleware


@pytest.fixture
def app():
    application = FastAPI()

    @application.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"item_id": item_id}

    @application.get("/health")
    def health():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="test-api",
        response_headers="emissions",
    )
    return application


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_tracks_routed_request(MockTracker, app):
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(
        emissions=0.001, duration=0.5, energy_consumed=0.002, emissions_rate=0.002
    )

    client = TestClient(app)
    response = client.get("/items/7")

    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.stop.assert_called_once()
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.001"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_applies_default_response_headers(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, response_headers="default")
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(
        emissions=0.001,
        duration=1.2,
        energy_consumed=0.003,
        emissions_rate=0.0008,
    )

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.001"
    assert response.headers["X-CodeCarbon-Duration-s"] == "1.2"
    assert response.headers["X-CodeCarbon-Energy-Consumed-kwh"] == "0.003"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_custom_header_formatter(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    def formatter(data, request):
        return {
            "X-CodeCarbon-Emissions-kg": f"{data.emissions:.4f}",
            "X-CodeCarbon-Route": request.url.path,
        }

    add_codecarbon_middleware(application, header_formatter=formatter)
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(emissions=0.001234)

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.0012"
    assert response.headers["X-CodeCarbon-Route"] == "/predict"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_skips_excluded_paths(MockTracker, app):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    MockTracker.assert_not_called()


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_include_emissions_header_deprecated(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, include_emissions_header=True)
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(emissions=0.002)

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.002"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_on_request_complete_callback(MockTracker):
    application = FastAPI()
    completed = []

    @application.get("/predict")
    def predict():
        return {"ok": True}

    def on_complete(request, response, emissions_data, task_name):
        completed.append(
            (request.url.path, response.status_code, emissions_data, task_name)
        )

    add_codecarbon_middleware(
        application,
        response_headers="emissions",
        on_request_complete=on_complete,
    )
    tracker_instance = MockTracker.return_value
    emissions = MagicMock(emissions=0.001)
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = emissions

    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    assert len(completed) == 1
    path, status, data, task_name = completed[0]
    assert path == "/predict"
    assert status == 200
    assert data is emissions
    assert task_name == "GET /predict"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_app_mode_uses_shared_tracker(MockTracker):
    application = FastAPI()
    tracker_instance = MagicMock()
    emissions = MagicMock(emissions=0.003, duration=0.8)
    tracker_instance.stop_task.return_value = emissions
    MockTracker.return_value = tracker_instance
    application.state.codecarbon_tracker = tracker_instance
    completed = []

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        tracking_mode="app",
        response_headers="emissions",
        on_request_complete=lambda request, response, data, task_name: completed.append(
            (request.url.path, data, task_name)
        ),
    )

    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    MockTracker.assert_not_called()
    tracker_instance.start_task.assert_called_once_with("GET /predict")
    tracker_instance.stop_task.assert_called_once_with("GET /predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.003"
    assert completed == [("/predict", emissions, "GET /predict")]


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_skips_headers_without_emissions_data(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, response_headers="emissions")
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.0
    tracker_instance.final_emissions_data = None

    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    assert "X-CodeCarbon-Emissions-kg" not in response.headers


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_app_mode_skips_callback_when_handler_raises(MockTracker):
    application = FastAPI()
    tracker_instance = MagicMock()
    tracker_instance.stop_task.return_value = MagicMock(emissions=0.001)
    MockTracker.return_value = tracker_instance
    application.state.codecarbon_tracker = tracker_instance
    completed = []

    @application.get("/fail")
    def fail():
        raise RuntimeError("boom")

    add_codecarbon_middleware(
        application,
        tracking_mode="app",
        on_request_complete=lambda *args: completed.append(args),
    )

    with pytest.raises(RuntimeError, match="boom"):
        TestClient(application, raise_server_exceptions=True).get("/fail")

    assert completed == []


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_app_mode_lazy_tracker(MockTracker):
    application = FastAPI()
    tracker_instance = MagicMock()
    emissions = MagicMock(emissions=0.005)
    tracker_instance.stop_task.return_value = emissions
    MockTracker.return_value = tracker_instance

    @application.get("/run")
    def run():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        tracking_mode="app",
        response_headers="emissions",
    )

    response = TestClient(application).get("/run")
    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.start_task.assert_called_once_with("GET /run")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.005"


@patch.object(cc_fastapi_middleware.asyncio, "to_thread")
@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_request_mode_uses_to_thread(MockTracker, mock_to_thread):
    application = FastAPI()
    tracker_instance = MockTracker.return_value
    emissions = MagicMock(emissions=0.001)
    tracker_instance.final_emissions_data = emissions

    async def run_sync(func, *args, **kwargs):
        return func(*args, **kwargs)

    mock_to_thread.side_effect = run_sync

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, response_headers="emissions")
    response = TestClient(application).get("/predict")

    assert response.status_code == 200
    assert mock_to_thread.call_count >= 2
    tracker_instance.start.assert_called_once()
    tracker_instance.stop.assert_called_once()


@patch.object(cc_fastapi_middleware.asyncio, "create_task")
@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_defer_measurement_skips_headers(MockTracker, mock_create_task):
    application = FastAPI()
    tracker_instance = MockTracker.return_value
    tracker_instance.final_emissions_data = MagicMock(emissions=0.001)

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        response_headers="emissions",
        defer_measurement=True,
    )
    response = TestClient(application).get("/predict")

    assert response.status_code == 200
    assert "X-CodeCarbon-Emissions-kg" not in response.headers
    mock_create_task.assert_called_once()


@patch.object(cc_fastapi_middleware.asyncio, "create_task")
@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_defer_measurement_runs_callback_via_background_task(
    MockTracker, mock_create_task
):
    application = FastAPI()
    completed = []
    tracker_instance = MockTracker.return_value
    emissions = MagicMock(emissions=0.001)
    tracker_instance.final_emissions_data = emissions

    async def run_finalize(coro):
        await coro

    mock_create_task.side_effect = lambda coro: asyncio.get_event_loop().create_task(
        run_finalize(coro)
    )

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        defer_measurement=True,
        on_request_complete=lambda request, response, data, task_name: completed.append(
            (request.url.path, data, task_name)
        ),
    )

    response = TestClient(application).get("/predict")

    assert response.status_code == 200
    assert completed == [("/predict", emissions, "GET /predict")]


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_include_endpoints_allowlist(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    @application.get("/metrics")
    def metrics():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        include=["GET /predict"],
        response_headers="emissions",
    )
    tracker_instance = MockTracker.return_value
    tracker_instance.final_emissions_data = MagicMock(emissions=0.001)

    client = TestClient(application)
    tracked = client.get("/predict")
    skipped = client.get("/metrics")

    assert tracked.status_code == 200
    assert "X-CodeCarbon-Emissions-kg" in tracked.headers
    assert skipped.status_code == 200
    assert "X-CodeCarbon-Emissions-kg" not in skipped.headers
    MockTracker.assert_called_once()


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_exclude_endpoints(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"tracked": True}

    @application.get("/admin")
    def admin():
        return {"admin": True}

    add_codecarbon_middleware(
        application,
        exclude=["GET /admin"],
        response_headers="emissions",
    )
    tracker_instance = MockTracker.return_value
    tracker_instance.final_emissions_data = MagicMock(emissions=0.001)

    client = TestClient(application)
    tracked = client.get("/predict")
    skipped = client.get("/admin")

    assert "X-CodeCarbon-Emissions-kg" in tracked.headers
    assert "X-CodeCarbon-Emissions-kg" not in skipped.headers
    MockTracker.assert_called_once()
