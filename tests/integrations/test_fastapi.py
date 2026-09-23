"""Tests for the FastAPI per-request energy attribution."""

import threading
import time
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.integrations.fastapi import (
    CodeCarbonMiddleware,
    EnergyAttributor,
    RequestEnergy,
)


def _invariant(attributor: EnergyAttributor) -> None:
    report = attributor.report()
    assert report["attributed_kwh"] + report["unattributed_kwh"] == pytest.approx(
        report["settled_kwh"], rel=1e-12, abs=1e-15
    )


def test_idle_windows_are_unattributed():
    attributor = EnergyAttributor()
    attributor.reset_window(0.0)
    attributor.on_window(1.0)
    assert attributor.unattributed_kwh == 1.0
    assert attributor.attributed_kwh == 0.0
    _invariant(attributor)


def test_window_energy_splits_by_overlap():
    attributor = EnergyAttributor()
    attributor.reset_window(0.0)
    early = attributor.begin("GET /a")
    time.sleep(0.02)
    late = attributor.begin("GET /b")
    time.sleep(0.02)
    attributor.on_window(1.0)

    # `early` overlapped roughly twice as much of the window as `late`.
    assert early.energy > late.energy
    assert early.energy + late.energy == pytest.approx(1.0)
    _invariant(attributor)


def test_backwards_counter_is_skipped_not_split():
    attributor = EnergyAttributor()
    attributor.reset_window(5.0)
    attributor.begin("GET /a")
    attributor.on_window(1.0)  # RAPL wrap
    assert attributor.windows_skipped == 1
    assert attributor.attributed_kwh == 0.0
    _invariant(attributor)


def test_unresolved_request_reports_no_energy():
    """A request that never covered a window gets None, not zero."""
    attributor = EnergyAttributor()
    attributor.reset_window(0.0)
    results = []
    state = attributor.begin("GET /fast")
    state.on_resolved = results.append
    attributor.end(state)
    attributor.close()

    assert [r.energy_kwh for r in results] == [None]


def test_invariant_holds_under_concurrency():
    """The core property: nothing is created or lost by the split."""
    attributor = EnergyAttributor()
    attributor.reset_window(0.0)
    results: list[RequestEnergy] = []  # list.append is atomic under the GIL
    stop = threading.Event()
    energy = 0.0

    def sampler():
        nonlocal energy
        while not stop.is_set():
            energy += 0.001
            attributor.on_window(energy)
            _invariant(attributor)
            time.sleep(0.002)

    def requester(i: int):
        for _ in range(20):
            state = attributor.begin(f"GET /{i % 3}")
            state.on_resolved = results.append
            time.sleep(0.001)
            attributor.end(state)

    sampler_thread = threading.Thread(target=sampler)
    sampler_thread.start()
    workers = [threading.Thread(target=requester, args=(i,)) for i in range(8)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    stop.set()
    sampler_thread.join()
    attributor.close()

    _invariant(attributor)
    assert len(results) == 8 * 20
    resolved = [r.energy_kwh for r in results if r.energy_kwh is not None]
    assert resolved, "no request ever covered a window"
    assert sum(resolved) == pytest.approx(attributor.attributed_kwh)


class _FakeTracker:
    """The slice of a tracker the middleware touches; windows closed by hand."""

    def __init__(self, started: bool = True) -> None:
        self._start_time = 0.0 if started else None
        self._total_energy = SimpleNamespace(kWh=0.0)
        self.observers = []

    def add_energy_window_observer(self, callback):
        self.observers.append(callback)

    def remove_energy_window_observer(self, callback):
        self.observers.remove(callback)

    def _carbon_intensity_kg_per_kwh(self):
        return 0.5

    def window(self, kwh: float) -> None:
        self._total_energy.kWh += kwh
        for callback in tuple(self.observers):
            callback(self._total_energy.kWh)


def _app(tracker, seen, *, lifespan=None):
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CodeCarbonMiddleware,
        tracker=tracker,
        on_request=lambda energy, kg, status: seen.append((energy, kg, status)),
    )

    @app.get("/work/{n}")
    def work(n: int):
        time.sleep(0.01)
        return {"n": n}

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    return app


def test_request_resolves_on_next_window():
    tracker, seen = _FakeTracker(), []
    with TestClient(_app(tracker, seen)) as client:
        assert client.get("/work/1").status_code == 200
        assert seen == []  # not known until a window closes
        tracker.window(1.0)
        energy, kg, status = seen[0]
    assert (energy.endpoint, status) == ("GET /work/{n}", 200)
    assert energy.energy_kwh == pytest.approx(1.0)
    assert kg == pytest.approx(0.5)


def test_app_raising_is_reported_as_500():
    tracker, seen = _FakeTracker(), []
    with TestClient(_app(tracker, seen), raise_server_exceptions=False) as client:
        assert client.get("/boom").status_code == 500
        tracker.window(1.0)
    assert seen[0][2] == 500


def test_close_on_shutdown_emits_pending():
    tracker, seen = _FakeTracker(), []
    with TestClient(_app(tracker, seen)) as client:
        client.get("/work/1")
    # Lifespan shutdown closed the middleware: no window ever covered it.
    assert [(e.energy_kwh, kg) for e, kg, _ in seen] == [(None, None)]
    assert tracker.observers == []


def test_tracker_not_started_records_nothing():
    tracker, seen = _FakeTracker(started=False), []
    with TestClient(_app(tracker, seen)) as client:
        for _ in range(5):
            assert client.get("/work/1").status_code == 200
    assert seen == []
    assert tracker.observers == []


def test_documented_lifespan_pattern():
    """The pattern from docs/how-to/examples.md, on an offline tracker."""
    seen = []

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        tracker = OfflineEmissionsTracker(
            country_iso_code="FRA",
            measure_power_secs=3600,  # windows are closed by hand below
            output_methods=[],
            allow_multiple_runs=True,
        )
        tracker.start()
        app.state.codecarbon_tracker = tracker
        yield
        tracker.stop()

    app = _app(None, seen, lifespan=lifespan)
    with TestClient(app) as client:
        assert client.get("/work/1").status_code == 200
        app.state.codecarbon_tracker._measure_power_and_energy()
        energy, kg, status = seen[0]

    assert (energy.endpoint, status) == ("GET /work/{n}", 200)
    assert energy.energy_kwh is not None and energy.energy_kwh > 0
    assert kg is not None and kg > 0
