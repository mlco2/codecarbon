"""Measurement tier tests. Every test injects known hardware/values.

Nothing here depends on what the test machine has (see PR #1365: a test that
asserted `< 90 W` passed on Apple Silicon and failed on Linux CI at 280 W).
"""

from __future__ import annotations

import dataclasses
import threading
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import codecarbon.integrations.fastapi.middleware as cc_middleware
from codecarbon.integrations.fastapi import (
    CodeCarbonMiddleware,
    MeasurementTier,
    add_codecarbon_middleware,
    detect_measurement_tier,
)
from codecarbon.integrations.fastapi.tiers import (
    NVML_MIN_AGGREGATION_SECONDS,
    hardware_tier,
)
from codecarbon.output_methods.emissions_data import EmissionsData


def _run_finalize_immediately(coro: Any) -> None:
    import asyncio
    from concurrent import futures

    def run_in_thread() -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    futures.ThreadPoolExecutor(max_workers=1).submit(run_in_thread).result()


@pytest.fixture
def finalize_deferred_immediately():
    """Deferred finalization runs inline so assertions see the result."""
    with patch.object(
        cc_middleware.CodeCarbonMiddleware,
        "_schedule_finalize",
        side_effect=_run_finalize_immediately,
    ):
        yield


def _cpu(mode: str) -> Any:
    return SimpleNamespace(_mode=mode)


class GPU:  # stand-in for codecarbon.external.hardware.GPU
    def __init__(self, devices: list[Any]) -> None:
        self.devices = SimpleNamespace(devices=devices)


class RAM:  # stand-in for codecarbon.external.ram.RAM
    pass


def _gpu(device_class_name: str, count: int = 1) -> Any:
    device_type = type(device_class_name, (), {})
    return GPU([device_type() for _ in range(count)])


def _ram() -> Any:
    return RAM()


def _emissions_data(**overrides: Any) -> EmissionsData:
    fields = {f.name: 0.0 for f in dataclasses.fields(EmissionsData)}
    fields.update(
        {
            "timestamp": "2026-01-01T00:00:00",
            "project_name": "test",
            "run_id": "run",
            "experiment_id": "exp",
            "country_name": "France",
            "country_iso_code": "FRA",
            "region": "",
            "cloud_provider": "",
            "cloud_region": "",
            "os": "test",
            "python_version": "3.13",
            "codecarbon_version": "test",
            "cpu_model": "test",
            "gpu_model": "",
        }
    )
    fields.update(overrides)
    return EmissionsData(**fields)


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("intel_rapl", MeasurementTier.MEASURED),
        ("constant", MeasurementTier.ESTIMATED),
        ("cpu_load", MeasurementTier.AGGREGATE_ONLY),
        ("apple_powermetrics", MeasurementTier.AGGREGATE_ONLY),
        ("windows_emi", MeasurementTier.AGGREGATE_ONLY),
        ("intel_power_gadget", MeasurementTier.AGGREGATE_ONLY),
        ("something_new", MeasurementTier.AGGREGATE_ONLY),
    ],
)
def test_cpu_mode_tiers(mode: str, expected: MeasurementTier) -> None:
    assert hardware_tier(_cpu(mode)) is expected


def test_nvml_needs_a_one_second_window() -> None:
    gpu = _gpu("NvidiaGPUDevice")
    assert hardware_tier(gpu, window_seconds=0.03) is MeasurementTier.AGGREGATE_ONLY
    assert (
        hardware_tier(gpu, window_seconds=NVML_MIN_AGGREGATION_SECONDS)
        is MeasurementTier.MEASURED
    )


def test_amd_gpu_is_unprobed_even_when_aggregating() -> None:
    assert hardware_tier(_gpu("AMDGPUDevice"), window_seconds=60) is (
        MeasurementTier.AGGREGATE_ONLY
    )


def test_ram_is_estimated_but_does_not_drag_rapl_down() -> None:
    assert hardware_tier(_ram()) is MeasurementTier.ESTIMATED
    detection = detect_measurement_tier([_cpu("intel_rapl"), _ram()])
    assert detection.tier is MeasurementTier.MEASURED
    assert dict(detection.components)["RAM"] is MeasurementTier.ESTIMATED


def test_weakest_component_wins() -> None:
    assert (
        detect_measurement_tier([_cpu("intel_rapl"), _gpu("NvidiaGPUDevice")]).tier
        is MeasurementTier.AGGREGATE_ONLY
    )
    assert (
        detect_measurement_tier([_cpu("constant"), _ram()]).tier
        is MeasurementTier.ESTIMATED
    )


def test_no_or_unknown_hardware_is_aggregate_only() -> None:
    assert detect_measurement_tier([]).tier is MeasurementTier.AGGREGATE_ONLY
    assert detect_measurement_tier(None).tier is MeasurementTier.AGGREGATE_ONLY
    assert detect_measurement_tier(MagicMock()).tier is MeasurementTier.AGGREGATE_ONLY
    assert detect_measurement_tier([object()]).tier is MeasurementTier.AGGREGATE_ONLY


def _build(middleware: CodeCarbonMiddleware, hardware, data, tracker=None):
    detection = detect_measurement_tier(hardware)
    return middleware._build_measurement(
        detection, "GET /predict", "GET /predict", data, tracker
    )


def test_measured_tier_reports_energy() -> None:
    middleware = CodeCarbonMiddleware(MagicMock())
    data = _emissions_data(duration=0.03, energy_consumed=1e-8, emissions=4e-9)
    measurement = _build(middleware, [_cpu("intel_rapl")], data)
    assert measurement.tier is MeasurementTier.MEASURED
    assert measurement.available
    assert measurement.energy_consumed == 1e-8
    middleware.shutdown_tracker_executor()


def test_zero_delta_is_unavailable_not_zero() -> None:
    """Zero is a factual claim that the request was free. Never report it."""
    middleware = CodeCarbonMiddleware(MagicMock())
    data = _emissions_data(duration=0.03, energy_consumed=0.0, emissions=0.0)
    measurement = _build(middleware, [_cpu("intel_rapl")], data)
    assert measurement.tier is MeasurementTier.MEASURED
    assert not measurement.available
    assert measurement.emissions is None
    assert measurement.energy_consumed is None
    assert "no completed sampling window" in measurement.unavailable_reason
    middleware.shutdown_tracker_executor()


def test_aggregate_only_has_no_per_request_energy_field() -> None:
    middleware = CodeCarbonMiddleware(MagicMock())
    data = _emissions_data(duration=0.03, energy_consumed=2.5e-8, emissions=1e-8)
    measurement = _build(middleware, [_cpu("cpu_load")], data)
    assert measurement.tier is MeasurementTier.AGGREGATE_ONLY
    assert measurement.emissions_data is None
    assert measurement.emissions is None
    assert "endpoint_totals()" in measurement.unavailable_reason
    middleware.shutdown_tracker_executor()


def test_estimated_tier_derives_energy_from_duration() -> None:
    middleware = CodeCarbonMiddleware(MagicMock())
    tracker = SimpleNamespace(
        _total_energy=SimpleNamespace(kWh=2.0), _total_emissions=1.0
    )  # intensity = 0.5 kg/kWh
    data = _emissions_data(duration=3600.0, cpu_power=100.0, ram_power=20.0)
    measurement = _build(middleware, [_cpu("constant"), _ram()], data, tracker)
    assert measurement.tier is MeasurementTier.ESTIMATED
    assert measurement.energy_consumed == pytest.approx(0.12)  # 120 W for 1 h
    assert measurement.emissions == pytest.approx(0.06)
    middleware.shutdown_tracker_executor()


def test_estimated_tier_without_known_intensity_is_unavailable() -> None:
    middleware = CodeCarbonMiddleware(MagicMock())
    tracker = SimpleNamespace(
        _total_energy=SimpleNamespace(kWh=0.0), _total_emissions=0.0
    )
    data = _emissions_data(duration=3600.0, cpu_power=100.0)
    measurement = _build(middleware, [_cpu("constant")], data, tracker)
    assert not measurement.available
    middleware.shutdown_tracker_executor()


def _app_with_tier(hardware, emissions_data, **middleware_kwargs):
    application = FastAPI()

    @application.get("/predict")
    def predict() -> dict[str, bool]:
        return {"ok": True}

    tracker = MagicMock()
    tracker._start_time = 1.0
    tracker._hardware = hardware
    tracker._measure_power_secs = 15.0
    tracker._total_energy = SimpleNamespace(kWh=1.0)
    tracker._total_emissions = 0.5
    tracker.mark_http_request_start.return_value = MagicMock(task_name="GET /predict")
    tracker.finish_http_request.return_value = emissions_data
    application.state.codecarbon_tracker = tracker
    add_codecarbon_middleware(application, **middleware_kwargs)
    return application, tracker


def test_gpu_machine_reports_per_request_energy(
    finalize_deferred_immediately,
) -> None:
    """The tracker's sampling window, not 0.0, decides the GPU tier."""
    data = _emissions_data(duration=0.03, energy_consumed=1e-6, emissions=5e-7)
    application, _ = _app_with_tier(
        [_cpu("intel_rapl"), _gpu("NvidiaGPUDevice")], data, on_request_complete=None
    )
    with TestClient(application) as client:
        assert client.get("/predict").status_code == 200
    middleware = application.state.codecarbon_middleware
    assert middleware.measurement_tier is MeasurementTier.MEASURED


def test_endpoint_totals_accumulate_in_aggregate_only_tier(
    finalize_deferred_immediately,
) -> None:
    data = _emissions_data(duration=0.03, energy_consumed=1e-6, emissions=5e-7)
    application, _ = _app_with_tier([_cpu("cpu_load")], data, on_request_complete=None)
    seen = []
    client = TestClient(application)
    for _ in range(3):
        assert client.get("/predict").status_code == 200
    middleware = application.state.codecarbon_middleware
    assert middleware.measurement_tier is MeasurementTier.AGGREGATE_ONLY
    totals = middleware.endpoint_totals()
    assert list(totals) == ["GET /predict"]
    entry = totals["GET /predict"]
    assert entry.count == 3
    assert entry.energy_consumed == pytest.approx(3e-6)
    assert entry.emissions == pytest.approx(1.5e-6)
    assert entry.tier is MeasurementTier.AGGREGATE_ONLY
    assert seen == []
    middleware.shutdown_tracker_executor()


def test_callback_and_request_state_carry_the_tier(
    finalize_deferred_immediately,
) -> None:
    seen = []
    data = _emissions_data(duration=0.03, energy_consumed=1e-6, emissions=5e-7)
    application, _ = _app_with_tier(
        [_cpu("cpu_load")],
        data,
        on_request_complete=lambda request, response, emissions_data, task: seen.append(
            (emissions_data, request.state.codecarbon)
        ),
    )
    assert TestClient(application).get("/predict").status_code == 200
    emissions_data, measurement = seen[0]
    assert emissions_data is None  # aggregate-only: no per-request energy
    assert measurement.tier is MeasurementTier.AGGREGATE_ONLY
    assert measurement.endpoint == "GET /predict"
    application.state.codecarbon_middleware.shutdown_tracker_executor()


def test_headers_are_off_by_default_and_carry_tier_when_enabled(
    finalize_deferred_immediately,
) -> None:
    data = _emissions_data(duration=0.03, energy_consumed=1e-6, emissions=5e-7)
    application, _ = _app_with_tier(
        [_cpu("intel_rapl")], data, on_request_complete=None
    )
    response = TestClient(application).get("/predict")
    assert "X-CodeCarbon-Emissions-kg" not in response.headers
    assert "X-CodeCarbon-Tier" not in response.headers
    application.state.codecarbon_middleware.shutdown_tracker_executor()

    application, _ = _app_with_tier(
        [_cpu("intel_rapl")],
        data,
        on_request_complete=None,
        response_headers=True,
    )
    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "5e-07"
    assert response.headers["X-CodeCarbon-Tier"] == "measured"
    application.state.codecarbon_middleware.shutdown_tracker_executor()


def test_headers_say_unavailable_instead_of_zero(
    finalize_deferred_immediately,
) -> None:
    data = _emissions_data(duration=0.03, energy_consumed=1e-6, emissions=5e-7)
    application, _ = _app_with_tier(
        [_cpu("cpu_load")],
        data,
        on_request_complete=None,
        response_headers=True,
    )
    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "unavailable"
    assert response.headers["X-CodeCarbon-Tier"] == "aggregate_only"
    application.state.codecarbon_middleware.shutdown_tracker_executor()


def test_tracker_tasks_map_stays_flat_over_10000_requests() -> None:
    """Real tracker methods, no scheduler: _tasks must not grow per request."""
    from codecarbon.emissions_tracker import EmissionsTracker

    tracker = object.__new__(EmissionsTracker)
    tracker._tasks = {}
    tracker._http_task_lock = threading.RLock()
    tracker._save_to_api = False
    tracker._output_handlers = []

    sizes = []
    for index in range(10_000):
        name = tracker._resolve_http_task_name("GET /predict")
        from codecarbon.external.task import Task

        tracker._tasks[name] = Task(task_name=name)
        tracker._tasks[name].is_active = False
        tracker.persist_completed_task(name)
        tracker.discard_task(name)
        if index % 1000 == 0:
            sizes.append(len(tracker._tasks))

    assert len(tracker._tasks) == 0
    assert sizes == [0] * len(sizes)


def test_middleware_discards_task_after_persisting(
    finalize_deferred_immediately,
) -> None:
    data = _emissions_data(duration=0.03, energy_consumed=1e-6, emissions=5e-7)
    application, tracker = _app_with_tier(
        [_cpu("intel_rapl")], data, on_request_complete=None
    )
    client = TestClient(application)
    for _ in range(5):
        client.get("/predict")
    assert tracker.persist_completed_task.call_count == 5
    assert tracker.discard_task.call_count == 5
    application.state.codecarbon_middleware.shutdown_tracker_executor()


@patch.object(cc_middleware, "EmissionsTracker")
def test_tier_is_resolved_once(MockTracker) -> None:
    middleware = CodeCarbonMiddleware(MagicMock())
    tracker = SimpleNamespace(_hardware=[_cpu("intel_rapl")])
    assert middleware.measurement_tier is None
    assert middleware._resolve_tier(tracker).tier is MeasurementTier.MEASURED
    tracker._hardware = [_cpu("cpu_load")]
    assert middleware._resolve_tier(tracker).tier is MeasurementTier.MEASURED
    assert middleware.measurement_tier is MeasurementTier.MEASURED
    middleware.shutdown_tracker_executor()
