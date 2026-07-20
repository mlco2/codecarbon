import asyncio
import logging
from concurrent import futures
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import codecarbon.integrations.fastapi.lifespan as cc_fastapi_lifespan
import codecarbon.integrations.fastapi.middleware as cc_fastapi_middleware
from codecarbon.external.logger import logger as codecarbon_logger
from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    create_codecarbon_lifespan,
    shutdown_codecarbon_middleware,
)
from codecarbon.integrations.fastapi.middleware import log_request_complete


def _run_finalize_immediately(coro: Any) -> None:
    def run_in_thread() -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    futures.ThreadPoolExecutor(max_workers=1).submit(run_in_thread).result()


@pytest.fixture(autouse=True)
def finalize_deferred_immediately():
    with patch.object(
        cc_fastapi_middleware.CodeCarbonMiddleware,
        "_schedule_finalize",
        side_effect=_run_finalize_immediately,
    ):
        yield


@pytest.fixture
def app():
    application = FastAPI()

    @application.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"item_id": item_id}

    @application.get("/health")
    def health():
        return {"ok": True}

    add_codecarbon_middleware(application, project_name="test-api")
    return application


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_tracks_routed_request(MockTracker, app) -> None:
    tracker_instance = MockTracker.return_value
    tracker_instance.stop_task.return_value = MagicMock(emissions=0.001)

    response = TestClient(app).get("/items/7")

    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.start_task.assert_called_once()
    tracker_instance.stop_task.assert_called_once()
    tracker_instance.persist_completed_task.assert_called_once_with("GET /items/7")


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_skips_excluded_paths(MockTracker, app) -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    MockTracker.assert_not_called()


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_on_request_complete_callback(MockTracker) -> None:
    application = FastAPI()
    completed = []

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        on_request_complete=lambda request, response, data, task_name: completed.append(
            (request.url.path, response.status_code, data, task_name)
        ),
    )
    tracker_instance = MockTracker.return_value
    emissions = MagicMock(emissions=0.001)
    tracker_instance.stop_task.return_value = emissions

    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    assert completed == [("/predict", 200, emissions, "GET /predict")]


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_uses_lifespan_tracker(MockTracker) -> None:
    application = FastAPI()
    tracker_instance = MagicMock()
    tracker_instance._start_time = 1.0
    baseline = MagicMock(task_name="GET /predict")
    emissions = MagicMock(emissions=0.003)
    tracker_instance.mark_http_request_start.return_value = baseline
    tracker_instance.finish_http_request.return_value = emissions
    application.state.codecarbon_tracker = tracker_instance
    completed = []

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        on_request_complete=lambda request, response, data, task_name: completed.append(
            (request.url.path, data, task_name)
        ),
    )

    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    MockTracker.assert_not_called()
    tracker_instance.mark_http_request_start.assert_called_once_with("GET /predict")
    tracker_instance.finish_http_request.assert_called_once_with(baseline)
    tracker_instance.persist_completed_task.assert_called_once_with("GET /predict")
    assert completed == [("/predict", emissions, "GET /predict")]


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_skips_callback_when_handler_raises(MockTracker) -> None:
    application = FastAPI()
    tracker_instance = MagicMock()
    tracker_instance.stop_task.return_value = MagicMock(emissions=0.001)
    application.state.codecarbon_tracker = tracker_instance
    completed = []

    @application.get("/fail")
    def fail():
        raise RuntimeError("boom")

    add_codecarbon_middleware(
        application,
        on_request_complete=lambda *args: completed.append(args),
    )

    with pytest.raises(RuntimeError, match="boom"):
        TestClient(application, raise_server_exceptions=True).get("/fail")

    assert completed == []


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_lazy_tracker(MockTracker) -> None:
    application = FastAPI()
    tracker_instance = MagicMock()
    tracker_instance.stop_task.return_value = MagicMock(emissions=0.005)
    MockTracker.return_value = tracker_instance

    @application.get("/run")
    def run():
        return {"ok": True}

    add_codecarbon_middleware(application)

    response = TestClient(application).get("/run")
    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.start_task.assert_called_once_with("GET /run")


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_no_logging_when_callback_disabled(MockTracker) -> None:
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, on_request_complete=None)
    MockTracker.return_value.stop_task.return_value = MagicMock(emissions=0.001)

    with patch.object(cc_fastapi_middleware.logger, "info") as mock_info:
        response = TestClient(application).get("/predict")

    assert response.status_code == 200
    mock_info.assert_not_called()


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_include_endpoints_allowlist(MockTracker) -> None:
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    @application.get("/metrics")
    def metrics():
        return {"ok": True}

    add_codecarbon_middleware(application, include=["GET /predict"])
    MockTracker.return_value.stop_task.return_value = MagicMock(emissions=0.001)

    client = TestClient(application)
    assert client.get("/predict").status_code == 200
    assert client.get("/metrics").status_code == 200
    MockTracker.assert_called_once()


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_exclude_endpoints(MockTracker) -> None:
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"tracked": True}

    @application.get("/admin")
    def admin():
        return {"admin": True}

    add_codecarbon_middleware(application, exclude=["GET /admin"])
    MockTracker.return_value.stop_task.return_value = MagicMock(emissions=0.001)

    client = TestClient(application)
    client.get("/predict")
    client.get("/admin")
    MockTracker.assert_called_once()


def test_log_request_complete_uses_codecarbon_logger() -> None:
    request = MagicMock(url=MagicMock(path="/predict"))
    response = MagicMock(status_code=200)
    emissions = MagicMock(emissions=0.0012)
    counter = _CodeCarbonLogCapture()
    previous_level = codecarbon_logger.level

    codecarbon_logger.setLevel(logging.INFO)
    cc_fastapi_middleware.logger.addHandler(counter)
    try:
        log_request_complete(request, response, emissions, "GET /predict")
    finally:
        cc_fastapi_middleware.logger.removeHandler(counter)
        codecarbon_logger.setLevel(previous_level)

    assert codecarbon_logger.name == "codecarbon"
    assert counter.emissions_lines == 1


class _CodeCarbonLogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.emissions_lines = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.name != "codecarbon":
            return
        message = record.getMessage()
        if message.startswith("CodeCarbon ") and "emissions=" in message:
            self.emissions_lines += 1


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
@patch.object(cc_fastapi_middleware.logger, "info")
def test_middleware_default_logs_after_request(mock_logger_info, MockTracker) -> None:
    application = FastAPI()
    MockTracker.return_value.stop_task.return_value = MagicMock(emissions=0.001)

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, project_name="test-api")
    response = TestClient(application).get("/predict")

    assert response.status_code == 200
    mock_logger_info.assert_called_once()


def test_add_codecarbon_middleware_registers_instance_on_app_state() -> None:
    application = FastAPI()
    add_codecarbon_middleware(application, project_name="shutdown-test")
    middleware = application.state.codecarbon_middleware
    middleware.shutdown_tracker_executor()
    with pytest.raises(RuntimeError, match="shutdown"):
        middleware._tracker_runner.submit_request(lambda: None)


def test_shutdown_codecarbon_middleware_helper() -> None:
    application = FastAPI()
    add_codecarbon_middleware(application, project_name="shutdown-test")
    shutdown_codecarbon_middleware(application)
    middleware = application.state.codecarbon_middleware
    with pytest.raises(RuntimeError, match="shutdown"):
        middleware._tracker_runner.submit_request(lambda: None)


@patch.object(cc_fastapi_lifespan, "EmissionsTracker")
def test_create_codecarbon_lifespan_shuts_down_middleware_executor(
    MockTracker: MagicMock,
) -> None:
    MockTracker.return_value = MagicMock()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application, project_name="lifespan-test"
        ):
            yield

    application = FastAPI(lifespan=lifespan)
    add_codecarbon_middleware(application, project_name="lifespan-test")

    with TestClient(application):
        pass

    middleware = application.state.codecarbon_middleware
    with pytest.raises(RuntimeError, match="shutdown"):
        middleware._tracker_runner.submit_request(lambda: None)


def test_middleware_real_tracker_logs_and_csv_on_lifespan_stop(tmp_path: Path) -> None:
    tracker_kwargs = {
        "save_to_file": True,
        "save_to_api": False,
        "save_to_logger": False,
        "output_dir": str(tmp_path),
        "measure_power_secs": 10,
        "allow_multiple_runs": True,
    }

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application,
            project_name="outputs-test",
            **tracker_kwargs,
        ):
            yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="outputs-test",
        tracker_kwargs=tracker_kwargs,
    )
    log_counter = _CodeCarbonLogCapture()
    cc_fastapi_middleware.logger.addHandler(log_counter)
    try:
        with TestClient(application) as client:
            assert client.get("/predict").status_code == 200
            assert client.get("/predict").status_code == 200
    finally:
        cc_fastapi_middleware.logger.removeHandler(log_counter)

    assert log_counter.emissions_lines == 2
    emissions_csv = tmp_path / "emissions.csv"
    assert emissions_csv.is_file()
    assert emissions_csv.stat().st_size > 0


@patch("codecarbon.output_methods.http.ApiClient")
def test_middleware_real_tracker_calls_api_per_request(
    MockApiClient, tmp_path: Path
) -> None:
    mock_api = MockApiClient.return_value
    mock_api.run_id = "test-run-id"
    mock_api.add_emission.return_value = True
    tracker_kwargs = {
        "save_to_file": False,
        "save_to_api": True,
        "save_to_logger": False,
        "output_dir": str(tmp_path),
        "experiment_id": "00000000-0000-0000-0000-000000000001",
        "api_key": "test-key",
        "measure_power_secs": 10,
        "allow_multiple_runs": True,
    }

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application,
            project_name="api-outputs-test",
            **tracker_kwargs,
        ):
            yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="api-outputs-test",
        tracker_kwargs=tracker_kwargs,
        on_request_complete=None,
    )
    with TestClient(application) as client:
        assert client.get("/predict").status_code == 200
        assert client.get("/predict").status_code == 200

    assert mock_api.add_emission.call_count >= 2
