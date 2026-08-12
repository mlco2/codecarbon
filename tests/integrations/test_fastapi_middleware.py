import asyncio
import logging
import threading
import time
from concurrent import futures
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
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
from codecarbon.integrations.fastapi.tiers import MeasurementTier, RequestMeasurement


def measured_hardware() -> list[Any]:
    """Injected hardware so tier detection never depends on the test machine."""
    return [SimpleNamespace(_mode="intel_rapl")]


def _configure_mock_running_tracker(
    tracker_instance: MagicMock,
    *,
    task_name: str = "GET /predict",
    emissions: float = 0.001,
) -> MagicMock:
    """Mock a started tracker that uses mark/finish HTTP paths (concurrency-safe)."""
    baseline = MagicMock(task_name=task_name)

    def mark_started() -> None:
        tracker_instance._start_time = 1.0

    tracker_instance.start.side_effect = mark_started
    tracker_instance._start_time = None
    tracker_instance.mark_http_request_start.return_value = baseline
    tracker_instance.finish_http_request.return_value = MagicMock(emissions=emissions)
    tracker_instance._hardware = measured_hardware()
    return baseline


def _run_finalize_immediately(coro: Any) -> None:
    def run_in_thread() -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    futures.ThreadPoolExecutor(max_workers=1).submit(run_in_thread).result()


@pytest.fixture(autouse=True)
def finalize_deferred_immediately(request):
    if request.node.get_closest_marker("no_immediate_finalize"):
        yield
        return
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
    _configure_mock_running_tracker(tracker_instance, task_name="GET /items/{item_id}")

    response = TestClient(app).get("/items/7")

    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.mark_http_request_start.assert_called_once()
    tracker_instance.finish_http_request.assert_called_once()
    # The route template is only known after Starlette routes the request.
    assert (
        tracker_instance.finish_http_request.call_args[0][1] == "GET /items/{item_id}"
    )
    tracker_instance.persist_completed_task.assert_called_once()


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
        on_request_complete=lambda request, status_code, data, task_name: completed.append(
            (request.url.path, status_code, data, task_name)
        ),
    )
    tracker_instance = MockTracker.return_value
    emissions = MagicMock(emissions=0.001)
    baseline = _configure_mock_running_tracker(
        tracker_instance, task_name="GET /predict", emissions=0.001
    )
    tracker_instance.finish_http_request.return_value = emissions

    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    assert completed == [("/predict", 200, emissions, baseline.task_name)]


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_uses_lifespan_tracker(MockTracker) -> None:
    application = FastAPI()
    tracker_instance = MagicMock()
    tracker_instance._start_time = 1.0
    tracker_instance._hardware = measured_hardware()
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
    tracker_instance.mark_http_request_start.assert_called_once_with("")
    tracker_instance.finish_http_request.assert_called_once_with(
        baseline, "GET /predict"
    )
    tracker_instance.persist_completed_task.assert_called_once_with("GET /predict")
    assert completed == [("/predict", emissions, "GET /predict")]


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_skips_callback_when_handler_raises(MockTracker) -> None:
    application = FastAPI()
    tracker_instance = MagicMock()
    tracker_instance._start_time = 1.0
    tracker_instance._hardware = measured_hardware()
    baseline = MagicMock(task_name="GET /fail")
    tracker_instance.mark_http_request_start.return_value = baseline
    tracker_instance.finish_http_request.return_value = MagicMock(emissions=0.001)
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
    _configure_mock_running_tracker(
        tracker_instance, task_name="GET /run", emissions=0.005
    )
    MockTracker.return_value = tracker_instance

    @application.get("/run")
    def run():
        return {"ok": True}

    add_codecarbon_middleware(application)

    response = TestClient(application).get("/run")
    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.mark_http_request_start.assert_called_once_with("")
    assert tracker_instance.finish_http_request.call_args[0][1] == "GET /run"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_no_logging_when_callback_disabled(MockTracker) -> None:
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, on_request_complete=None)
    _configure_mock_running_tracker(MockTracker.return_value)

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
    _configure_mock_running_tracker(MockTracker.return_value)

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
    _configure_mock_running_tracker(MockTracker.return_value)

    client = TestClient(application)
    client.get("/predict")
    client.get("/admin")
    MockTracker.assert_called_once()


def test_log_request_complete_uses_codecarbon_logger() -> None:
    request = MagicMock(url=MagicMock(path="/predict"))
    emissions = MagicMock(emissions=0.0012)
    counter = _CodeCarbonLogCapture()
    previous_level = codecarbon_logger.level

    codecarbon_logger.setLevel(logging.INFO)
    cc_fastapi_middleware.logger.addHandler(counter)
    try:
        log_request_complete(request, 200, emissions, "GET /predict")
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
    _configure_mock_running_tracker(MockTracker.return_value)

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
    with TestClient(application):
        pass
    middleware = application.state.codecarbon_middleware
    middleware.shutdown_tracker_executor()
    with pytest.raises(RuntimeError, match="shutdown"):
        middleware._tracker_runner.submit(lambda: None)


def test_shutdown_codecarbon_middleware_helper() -> None:
    application = FastAPI()
    add_codecarbon_middleware(application, project_name="shutdown-test")
    with TestClient(application):
        pass
    shutdown_codecarbon_middleware(application)
    middleware = application.state.codecarbon_middleware
    with pytest.raises(RuntimeError, match="shutdown"):
        middleware._tracker_runner.submit(lambda: None)


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
        middleware._tracker_runner.submit(lambda: None)


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


def test_finalize_measures_before_on_request_complete() -> None:
    order: list[str] = []

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application,
            project_name="measure-order",
            save_to_file=False,
            save_to_api=False,
            allow_multiple_runs=True,
            measure_power_secs=10,
        ):
            yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    def on_complete(request, response, emissions_data, task_name) -> None:
        order.append("callback")

    add_codecarbon_middleware(
        application,
        project_name="measure-order",
        on_request_complete=on_complete,
        tracker_kwargs={
            "save_to_file": False,
            "save_to_api": False,
            "allow_multiple_runs": True,
            "measure_power_secs": 10,
        },
    )

    with TestClient(application) as client:
        tracker = application.state.codecarbon_tracker
        tracker._last_measured_time = 0.0
        original = tracker._run_power_measurement

        def wrapped() -> None:
            order.append("measure")
            return original()

        with patch.object(tracker, "_run_power_measurement", side_effect=wrapped):
            assert client.get("/predict").status_code == 200

    assert order == ["measure", "callback"]


def test_concurrent_same_route_gets_distinct_task_names() -> None:
    task_names: list[str] = []

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application,
            project_name="concurrent-test",
            save_to_file=False,
            save_to_api=False,
            allow_multiple_runs=True,
            measure_power_secs=10,
        ):
            yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    def on_complete(request, response, emissions_data, task_name) -> None:
        task_names.append(task_name)

    add_codecarbon_middleware(
        application,
        project_name="concurrent-test",
        on_request_complete=on_complete,
        tracker_kwargs={
            "save_to_file": False,
            "save_to_api": False,
            "allow_multiple_runs": True,
            "measure_power_secs": 10,
        },
    )

    with TestClient(application) as client:
        tracker = application.state.codecarbon_tracker
        baselines = [
            tracker.mark_http_request_start("GET /predict"),
            tracker.mark_http_request_start("GET /predict"),
        ]
        assert baselines[0].task_name != baselines[1].task_name
        assert baselines[0].task_name.startswith("GET /predict")
        assert "GET /predict" in baselines[1].task_name
        for baseline in baselines:
            tracker.finish_http_request(baseline)

        assert client.get("/predict").status_code == 200
        assert client.get("/predict").status_code == 200

    assert len(task_names) == 2
    assert all(name.startswith("GET /predict") for name in task_names)


def test_concurrent_live_tracker_no_stop_task_errors() -> None:
    """Concurrent HTTP requests must not trigger stop_task on mark_http_request tasks."""
    import logging

    from starlette.testclient import TestClient

    error_messages: list[str] = []

    class _ErrorHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if (
                record.levelno >= logging.ERROR
                and "_active_task_emissions_at_start" in record.getMessage()
            ):
                error_messages.append(record.getMessage())

    handler = _ErrorHandler()
    cc_fastapi_middleware.logger.addHandler(handler)
    try:

        @asynccontextmanager
        async def lifespan(application: FastAPI):
            async with create_codecarbon_lifespan(
                application,
                project_name="concurrent-live",
                save_to_file=False,
                save_to_api=False,
                allow_multiple_runs=True,
                measure_power_secs=2,
            ):
                yield

        application = FastAPI(lifespan=lifespan)

        @application.get("/predict")
        def predict() -> dict[str, bool]:
            return {"ok": True}

        add_codecarbon_middleware(
            application,
            project_name="concurrent-live",
            on_request_complete=None,
            tracker_kwargs={
                "save_to_file": False,
                "save_to_api": False,
                "allow_multiple_runs": True,
                "measure_power_secs": 2,
            },
        )

        with TestClient(application) as client:
            for _ in range(12):
                assert client.get("/predict").status_code == 200

        assert error_messages == []
    finally:
        cc_fastapi_middleware.logger.removeHandler(handler)


def test_concurrent_lazy_tracker_without_lifespan() -> None:
    """Lazy-started tracker must use mark/finish, not start_task/stop_task, under load."""
    import concurrent.futures
    import logging

    error_messages: list[str] = []

    class _ErrorHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if (
                record.levelno >= logging.ERROR
                and "_active_task_emissions_at_start" in record.getMessage()
            ):
                error_messages.append(record.getMessage())

    handler = _ErrorHandler()
    cc_fastapi_middleware.logger.addHandler(handler)
    try:
        application = FastAPI()

        @application.get("/predict")
        def predict() -> dict[str, bool]:
            return {"ok": True}

        add_codecarbon_middleware(
            application,
            project_name="lazy-concurrent",
            on_request_complete=None,
            tracker_kwargs={
                "save_to_file": False,
                "save_to_api": False,
                "allow_multiple_runs": True,
                "measure_power_secs": 2,
            },
        )

        with TestClient(application) as client:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(client.get, "/predict") for _ in range(16)]
                for future in futures:
                    assert future.result().status_code == 200

        assert error_messages == []
    finally:
        # No lifespan here, so nothing else stops the lazily created tracker.
        cc_fastapi_middleware.shutdown_codecarbon_middleware(application)
        cc_fastapi_middleware.logger.removeHandler(handler)


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_response_headers_sync_mode_injects_emissions_header(MockTracker) -> None:
    _configure_mock_running_tracker(MockTracker.return_value, emissions=0.0012)
    MockTracker.return_value.finish_http_request.return_value = MagicMock(
        emissions=0.0012
    )
    application = FastAPI()

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="headers-test",
        response_headers=True,
        on_request_complete=None,
    )
    response = TestClient(application).get("/predict")
    assert response.status_code == 200
    assert response.headers.get("X-CodeCarbon-Emissions-kg") == "0.0012"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_default_mode_has_no_emission_headers(MockTracker) -> None:
    _configure_mock_running_tracker(MockTracker.return_value, emissions=0.0012)
    application = FastAPI()

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    add_codecarbon_middleware(
        application, project_name="no-headers", on_request_complete=None
    )
    response = TestClient(application).get("/predict")
    assert "X-CodeCarbon-Emissions-kg" not in response.headers


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_include_background_tasks_false_finalizes_before_background(
    MockTracker,
) -> None:
    from fastapi import BackgroundTasks

    order: list[str] = []
    mock_tracker = MockTracker.return_value
    _configure_mock_running_tracker(mock_tracker)

    def finish_http_request(*args: Any, **kwargs: Any) -> MagicMock:
        order.append("finalize")
        return MagicMock(emissions=0.001)

    mock_tracker.finish_http_request.side_effect = finish_http_request
    application = FastAPI()

    @application.get("/predict")
    def predict_with_bg(background_tasks: BackgroundTasks) -> dict[str, bool]:
        def work() -> None:
            order.append("background")

        background_tasks.add_task(work)
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="bg-false",
        include_background_tasks=False,
        on_request_complete=None,
    )
    assert TestClient(application).get("/predict").status_code == 200
    assert "finalize" in order
    assert "background" in order
    assert order.index("finalize") < order.index("background")


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_include_background_tasks_true_finalizes_after_background(MockTracker) -> None:
    from fastapi import BackgroundTasks

    order: list[str] = []
    mock_tracker = MockTracker.return_value
    _configure_mock_running_tracker(mock_tracker)

    def finish_http_request(*args: Any, **kwargs: Any) -> MagicMock:
        order.append("finalize")
        return MagicMock(emissions=0.001)

    mock_tracker.finish_http_request.side_effect = finish_http_request
    application = FastAPI()

    @application.get("/predict")
    def predict_with_bg(background_tasks: BackgroundTasks) -> dict[str, bool]:
        def work() -> None:
            order.append("background")

        background_tasks.add_task(work)
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="bg-true",
        include_background_tasks=True,
        on_request_complete=None,
    )
    assert TestClient(application).get("/predict").status_code == 200
    assert "background" in order
    assert "finalize" in order
    assert order.index("background") < order.index("finalize")


def test_resolve_header_fields_and_header_names() -> None:
    from codecarbon.integrations.fastapi.middleware import (
        _codecarbon_header_name,
        _inject_emission_headers,
        _resolve_header_fields,
    )

    assert _resolve_header_fields(None) == ()
    assert _resolve_header_fields(True) == ("emissions",)
    assert _resolve_header_fields(["emissions", "duration"]) == (
        "emissions",
        "duration",
    )
    assert (
        _codecarbon_header_name("energy_consumed") == "X-CodeCarbon-Energy-Consumed-kwh"
    )

    message = {"type": "http.response.start", "headers": []}
    assert _inject_emission_headers(message, None, ["emissions"]) is message

    emissions = MagicMock(spec=["emissions", "duration"])
    emissions.emissions = 0.0012
    emissions.duration = 1.5
    measurement = RequestMeasurement(
        tier=MeasurementTier.MEASURED,
        task_name="GET /predict",
        endpoint="GET /predict",
        duration=1.5,
        emissions_data=emissions,
    )
    injected = _inject_emission_headers(
        message, measurement, ["emissions", "unknown_field", "duration"]
    )
    header_names = {name.decode() for name, _ in injected["headers"]}
    assert header_names == {
        "X-CodeCarbon-Tier",
        "X-CodeCarbon-Emissions-kg",
        "X-CodeCarbon-Duration-s",
    }


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_task_name_formatter(MockTracker) -> None:
    application = FastAPI()
    _configure_mock_running_tracker(
        MockTracker.return_value, task_name="custom-/predict"
    )

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        task_name_formatter=lambda request: f"custom-{request.url.path}",
        on_request_complete=None,
    )
    assert TestClient(application).get("/predict").status_code == 200
    assert (
        MockTracker.return_value.finish_http_request.call_args[0][1]
        == "custom-/predict"
    )


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_response_headers_custom_field_list(MockTracker) -> None:
    application = FastAPI()
    emissions = MagicMock(emissions=0.0012, duration=1.5)
    _configure_mock_running_tracker(MockTracker.return_value)
    MockTracker.return_value.finish_http_request.return_value = emissions

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        response_headers=["emissions", "duration"],
        on_request_complete=None,
    )
    response = TestClient(application).get("/predict")
    assert response.headers.get("X-CodeCarbon-Emissions-kg") == "0.0012"
    assert response.headers.get("X-CodeCarbon-Duration-s") == "1.5"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_websocket_scope_is_not_tracked(MockTracker) -> None:
    from unittest.mock import AsyncMock

    inner = AsyncMock()

    async def run() -> None:
        middleware = cc_fastapi_middleware.CodeCarbonMiddleware(inner)
        await middleware({"type": "websocket"}, MagicMock(), MagicMock())

    asyncio.run(run())
    inner.assert_awaited_once()
    MockTracker.assert_not_called()


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_end_of_body_mode_reraises_handler_error(MockTracker) -> None:
    application = FastAPI()
    _configure_mock_running_tracker(MockTracker.return_value)

    @application.get("/fail")
    def fail() -> None:
        raise RuntimeError("boom")

    add_codecarbon_middleware(
        application,
        include_background_tasks=False,
        on_request_complete=None,
    )
    with pytest.raises(RuntimeError, match="boom"):
        TestClient(application, raise_server_exceptions=True).get("/fail")


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_sync_headers_mode_reraises_handler_error(MockTracker) -> None:
    application = FastAPI()
    _configure_mock_running_tracker(MockTracker.return_value)

    @application.get("/fail")
    def fail() -> None:
        raise RuntimeError("boom")

    add_codecarbon_middleware(
        application,
        response_headers=True,
        on_request_complete=None,
    )
    with pytest.raises(RuntimeError, match="boom"):
        TestClient(application, raise_server_exceptions=True).get("/fail")


@pytest.mark.no_immediate_finalize
def test_schedule_finalize_logs_measurement_failure() -> None:
    application = FastAPI()
    middleware = cc_fastapi_middleware.CodeCarbonMiddleware(application)

    async def fail() -> None:
        raise RuntimeError("measurement failed")

    async def run() -> None:
        scheduled: list[asyncio.Task[None]] = []

        def track_create_task(coro: Any) -> asyncio.Task[None]:
            task = asyncio.get_running_loop().create_task(coro)
            scheduled.append(task)
            return task

        with patch("asyncio.create_task", side_effect=track_create_task):
            with patch.object(
                cc_fastapi_middleware.logger, "exception"
            ) as mock_exception:
                middleware._schedule_finalize(fail())
                await asyncio.gather(*scheduled)
                mock_exception.assert_called_once()

    asyncio.run(run())


@pytest.mark.no_immediate_finalize
def test_real_tracker_reports_sub_second_request_duration() -> None:
    """End-to-end: real tracker, real deferred finalize, plausible duration.

    Everything else here mocks the tracker and finalizes inline, which is how a
    negative per-request duration went unnoticed.
    """
    completed: list[Any] = []
    measured = threading.Event()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application,
            project_name="e2e-duration",
            save_to_file=False,
            save_to_api=False,
            save_to_logger=False,
            measure_power_secs=10,
            allow_multiple_runs=True,
        ):
            yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    def on_complete(request, status_code, data, task_name) -> None:
        completed.append(data)
        measured.set()

    add_codecarbon_middleware(
        application, project_name="e2e-duration", on_request_complete=on_complete
    )

    with TestClient(application) as client:
        # Let the tracker run for a while so an absolute-vs-delta duration bug
        # shows up as a negative or multi-second request duration.
        time.sleep(1.5)
        # First request absorbs the metadata snapshot and a stale power sample.
        assert client.get("/predict").status_code == 200
        assert measured.wait(10)
        measured.clear()
        assert client.get("/predict").status_code == 200
        assert measured.wait(10)

    assert 0 < completed[-1].duration < 1
