"""Tests for the FastAPI per-request energy attribution."""

import threading
import time
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from codecarbon.emissions_tracker import OfflineEmissionsTracker, WindowSample
from codecarbon.external.hardware import CPU
from codecarbon.integrations.fastapi import (
    CodeCarbonMiddleware,
    EnergyAttributor,
    RequestEnergy,
)


def _sample(total: float, *, cpu: float | None = None, gpu: float = 0.0, **kw):
    """A window sample; by default all energy is dynamic CPU energy."""
    fields = dict(
        timestamp=time.perf_counter(),
        total_kwh=total,
        cpu_kwh=total - gpu if cpu is None else cpu,
        gpu_kwh=gpu,
        ram_kwh=0.0,
        cpu_quality="measured",
        gpu_quality=None,
        cpu_idle_w=0.0,
        cpu_per_process=False,
    )
    fields.update(kw)
    return WindowSample(**fields)


def _invariant(attributor: EnergyAttributor) -> None:
    report = attributor.report()
    buckets = ("attributed_kwh", "idle_kwh", "unattributed_kwh")
    assert sum(report[b] for b in buckets) == pytest.approx(
        report["settled_kwh"], rel=1e-12, abs=1e-15
    )


def test_idle_windows_are_unattributed():
    attributor = EnergyAttributor()
    attributor.reset_window(_sample(0.0))
    attributor.on_window(_sample(1.0))
    assert attributor.unattributed_kwh == 1.0
    assert attributor.attributed_kwh == 0.0
    _invariant(attributor)


def test_window_energy_splits_by_overlap():
    attributor = EnergyAttributor()
    attributor.reset_window(_sample(0.0))
    early = attributor.begin("GET /a")
    time.sleep(0.02)
    late = attributor.begin("GET /b")
    time.sleep(0.02)
    attributor.on_window(_sample(1.0))

    # `early` overlapped roughly twice as much of the window as `late`.
    assert early.energy > late.energy
    assert early.energy + late.energy == pytest.approx(1.0)
    _invariant(attributor)


def test_backwards_counter_is_skipped_not_split():
    attributor = EnergyAttributor()
    attributor.reset_window(_sample(5.0))
    attributor.begin("GET /a")
    attributor.on_window(_sample(1.0))  # RAPL wrap
    assert attributor.windows_skipped == 1
    assert attributor.attributed_kwh == 0.0
    _invariant(attributor)


def test_unresolved_request_reports_no_energy():
    """A request that never covered a window gets None, not zero."""
    attributor = EnergyAttributor()
    attributor.reset_window(_sample(0.0))
    results = []
    state = attributor.begin("GET /fast")
    state.on_resolved = results.append
    attributor.end(state)
    attributor.close()

    assert [r.energy_kwh for r in results] == [None]


def test_invariant_holds_under_concurrency():
    """The core property: nothing is created or lost by the split."""
    attributor = EnergyAttributor()
    attributor.reset_window(_sample(0.0))
    results: list[RequestEnergy] = []  # list.append is atomic under the GIL
    stop = threading.Event()
    energy = 0.0

    def sampler():
        nonlocal energy
        while not stop.is_set():
            energy += 0.001
            attributor.on_window(_sample(energy))
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


class _FakeTimes:
    """Scripted ``(process, busy, total)`` CPU seconds; advanced by hand."""

    def __init__(self) -> None:
        self.process = self.busy = self.total = 0.0

    def advance(self, *, process=0.0, busy=0.0, total=1.0) -> None:
        self.process += process
        self.busy += busy
        self.total += total

    def __call__(self):
        return self.process, self.busy, self.total


def _kwh(watts: float, seconds: float) -> float:
    return watts * seconds / 3.6e6


def test_idle_power_is_the_rolling_minimum():
    attributor = EnergyAttributor(cpu_times=_FakeTimes())
    attributor.reset_window(_sample(0.0, timestamp=0.0, cpu_idle_w=None))
    attributor.on_window(_sample(_kwh(10, 1), timestamp=1.0, cpu_idle_w=None))
    # First window: its own power is the only minimum, so it is all idle.
    assert attributor.idle_kwh == pytest.approx(_kwh(10, 1))
    attributor.on_window(_sample(_kwh(10 + 40, 1), timestamp=2.0, cpu_idle_w=None))
    assert attributor.unattributed_kwh == pytest.approx(_kwh(30, 1))
    assert attributor.report()["idle_power_w"]["cpu"] == pytest.approx(10)
    _invariant(attributor)


def test_idle_power_uses_a_good_regression_intercept():
    """Never idle, so the minimum (13 W) overestimates; the fit finds 5 W."""
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0, cpu_idle_w=None))
    energy = 0.0
    for i in range(1, 31):
        util = 0.2 + 0.6 * (i % 5) / 4
        times.advance(busy=util)
        energy += _kwh(5 + 40 * util, 1)
        attributor.on_window(_sample(energy, timestamp=float(i), cpu_idle_w=None))
    assert attributor.report()["idle_power_w"]["cpu"] == pytest.approx(5)
    _invariant(attributor)


def test_idle_rolling_minimum_forgets_old_windows():
    attributor = EnergyAttributor(cpu_times=_FakeTimes(), idle_horizon_s=10)
    attributor.reset_window(_sample(0.0, timestamp=0.0, cpu_idle_w=None))
    attributor.on_window(_sample(_kwh(10, 1), timestamp=1.0, cpu_idle_w=None))
    energy = _kwh(10, 1)
    for t in range(2, 20):
        energy += _kwh(20, 1)
        attributor.on_window(_sample(energy, timestamp=float(t), cpu_idle_w=None))
    assert attributor.report()["idle_power_w"]["cpu"] == pytest.approx(20)


def test_analytic_idle_and_ram_go_to_idle_bucket():
    """Load mode fixes idle at 0.1 * TDP; RAM is never charged to requests."""
    attributor = EnergyAttributor(cpu_times=_FakeTimes())
    attributor.reset_window(_sample(0.0, timestamp=0.0))
    state = attributor.begin("GET /a")
    state.start = 0.0
    cpu, ram = _kwh(25, 2), _kwh(3, 2)
    attributor.on_window(
        _sample(cpu + ram, cpu=cpu, ram_kwh=ram, timestamp=2.0, cpu_idle_w=10.0)
    )
    assert state.energy == pytest.approx(_kwh(15, 2))
    assert attributor.idle_kwh == pytest.approx(_kwh(10 + 3, 2))
    _invariant(attributor)


def test_gpu_idle_is_estimated_separately():
    attributor = EnergyAttributor(cpu_times=_FakeTimes())
    gpu = dict(gpu_quality="measured")
    attributor.reset_window(_sample(0.0, timestamp=0.0, **gpu))
    attributor.on_window(_sample(_kwh(50, 1), gpu=_kwh(50, 1), timestamp=1.0, **gpu))
    attributor.on_window(
        _sample(_kwh(50 + 100, 1), gpu=_kwh(50 + 100, 1), timestamp=2.0, **gpu)
    )
    assert attributor.report()["idle_power_w"]["gpu"] == pytest.approx(50)
    assert attributor.unattributed_kwh == pytest.approx(_kwh(50, 1))
    _invariant(attributor)


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

    def _window_sample(self):
        return _sample(self._total_energy.kWh)

    def window(self, kwh: float) -> None:
        self._total_energy.kWh += kwh
        for callback in tuple(self.observers):
            callback(self._window_sample())


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


def test_window_sample_reports_components_and_quality():
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=3600,
        output_methods=[],
        allow_multiple_runs=True,
        force_mode_cpu_load=True,
    )
    samples = []
    tracker.add_energy_window_observer(samples.append)
    tracker.start()
    try:
        tracker._measure_power_and_energy()
    finally:
        tracker.stop()
    sample = samples[0]
    assert sample.cpu_quality == "modeled"
    (cpu,) = [h for h in tracker._hardware if isinstance(h, CPU)]
    assert sample.cpu_idle_w == pytest.approx(0.1 * cpu._tdp * tracker._pue)
    parts = sample.cpu_kwh + sample.gpu_kwh + sample.ram_kwh
    assert sample.total_kwh == pytest.approx(parts)
    assert sample.total_kwh > 0
