"""Tests for the FastAPI per-request energy attribution."""

import asyncio
import threading
import time
import types
from contextlib import asynccontextmanager
from types import SimpleNamespace

import psutil
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
from codecarbon.integrations.fastapi.attribution import _Meter, _Metered


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
        cpu_w_per_busy_cpu=None,
        cpu_per_process=False,
    )
    fields.update(kw)
    return WindowSample(**fields)


def _all_ours():
    """CPU times where every busy second is this process's (share 1)."""
    n = 0.0

    def times():
        nonlocal n
        n += 1.0
        return n, n, 2 * n

    return times


def _invariant(attributor: EnergyAttributor) -> None:
    report = attributor.report()
    buckets = (
        "attributed_kwh",
        "idle_kwh",
        "other_processes_kwh",
        "process_unattributed_kwh",
        "unattributed_kwh",
    )
    assert sum(report[b] for b in buckets) == pytest.approx(
        report["settled_kwh"], rel=1e-12, abs=1e-15
    )


def test_idle_windows_are_unattributed():
    attributor = EnergyAttributor(cpu_times=_all_ours())
    attributor.reset_window(_sample(0.0))
    attributor.on_window(_sample(1.0))
    assert attributor.unattributed_kwh == 1.0
    assert attributor.attributed_kwh == 0.0
    _invariant(attributor)


def _begin(attributor, endpoint="GET /a", *, start=0.0, cpu_s=0.0):
    """A request that started at ``start`` and used ``cpu_s`` of CPU so far."""
    meter = _Meter()
    meter.ns = int(cpu_s * 1e9)
    state = attributor.begin(endpoint, meter)
    state.start = start
    return state


def test_cpu_energy_splits_by_cpu_time():
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0))
    busy = _begin(attributor, "GET /busy", cpu_s=0.6)
    waiting = _begin(attributor, "GET /io", cpu_s=0.0)
    times.advance(process=1.0, busy=1.0)
    attributor.on_window(_sample(_kwh(100, 1), timestamp=1.0))
    # The process used 1 s of CPU; the meters account for 0.6 s of it.
    assert busy.energy == pytest.approx(_kwh(60, 1))
    assert waiting.energy == 0.0
    assert attributor.process_unattributed_kwh == pytest.approx(_kwh(40, 1))
    # Only the CPU time since the last window counts in the next one.
    busy.meter.ns += int(0.5e9)
    times.advance(process=0.5, busy=0.5)
    attributor.on_window(_sample(_kwh(150, 1), timestamp=2.0))
    assert busy.energy == pytest.approx(_kwh(110, 1))
    _invariant(attributor)


def test_meters_claiming_more_than_the_process_are_scaled_down():
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0))
    a = _begin(attributor, cpu_s=0.9)
    b = _begin(attributor, cpu_s=0.3)
    times.advance(process=1.0, busy=1.0)
    attributor.on_window(_sample(_kwh(100, 1), timestamp=1.0))
    assert a.energy == pytest.approx(_kwh(75, 1))
    assert b.energy == pytest.approx(_kwh(25, 1))
    assert attributor.process_unattributed_kwh == pytest.approx(0.0, abs=1e-18)
    _invariant(attributor)


def test_gpu_energy_splits_by_overlap():
    attributor = EnergyAttributor(cpu_times=_all_ours())
    gpu = dict(gpu_quality="measured")
    attributor.reset_window(_sample(0.0, timestamp=0.0, **gpu))
    attributor.on_window(_sample(0.0, timestamp=1.0, **gpu))  # GPU idles at 0 W
    early = _begin(attributor, "GET /a", start=1.0)
    late = _begin(attributor, "GET /b", start=2.0)
    attributor.on_window(_sample(_kwh(90, 2), gpu=_kwh(90, 2), timestamp=3.0, **gpu))
    # `early` overlapped twice as much of the window as `late`.
    assert early.gpu_energy == pytest.approx(_kwh(120, 1))
    assert late.gpu_energy == pytest.approx(_kwh(60, 1))
    assert early.energy == late.energy == 0.0  # no CPU time metered
    _invariant(attributor)


def test_request_reports_method_and_weakest_quality():
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    gpu = dict(gpu_quality="measured", cpu_quality="modeled")
    attributor.reset_window(_sample(0.0, timestamp=0.0, **gpu))
    attributor.on_window(_sample(0.0, timestamp=1.0, **gpu))
    results = []
    both = _begin(attributor, "GET /both", start=1.0, cpu_s=0.5)
    gpu_only = _begin(attributor, "GET /gpu", start=1.0)
    both.on_resolved = gpu_only.on_resolved = results.append
    attributor.end(both)
    attributor.end(gpu_only)
    times.advance(process=1.0, busy=1.0)
    attributor.on_window(_sample(_kwh(20, 1), gpu=_kwh(10, 1), timestamp=2.0, **gpu))
    by_endpoint = {r.endpoint: r for r in results}
    assert by_endpoint["GET /both"].attribution_method == "mixed"
    assert by_endpoint["GET /both"].energy_kwh == pytest.approx(_kwh(5, 1))
    assert by_endpoint["GET /both"].gpu_kwh == pytest.approx(_kwh(5, 1))
    assert by_endpoint["GET /both"].cpu_seconds == 0.5
    assert by_endpoint["GET /gpu"].attribution_method == "wall"
    assert {r.quality for r in results} == {"modeled"}
    assert attributor.report()["quality"] == {"cpu": "modeled", "gpu": "measured"}


def test_backwards_counter_is_skipped_not_split():
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(5.0, timestamp=0.0))
    state = _begin(attributor, cpu_s=1.0)
    times.advance(process=1.0, busy=1.0)
    attributor.on_window(_sample(1.0, timestamp=1.0))  # RAPL wrap
    assert attributor.windows_skipped == 1
    assert attributor.attributed_kwh == 0.0
    # The skipped window's CPU time is not charged to the next one.
    times.advance(process=1.0, busy=1.0)
    attributor.on_window(_sample(1.0 + _kwh(100, 1), timestamp=2.0))
    assert state.energy == 0.0
    _invariant(attributor)


def test_unresolved_request_reports_no_energy():
    """A request that never covered a window gets None, not zero."""
    attributor = EnergyAttributor(cpu_times=_all_ours())
    attributor.reset_window(_sample(0.0))
    results = []
    state = attributor.begin("GET /fast")
    state.on_resolved = results.append
    attributor.end(state)
    attributor.close()

    assert [r.energy_kwh for r in results] == [None]


def test_invariant_holds_under_concurrency():
    """The core property: nothing is created or lost by the split."""
    attributor = EnergyAttributor(cpu_times=_all_ours())
    attributor.reset_window(_sample(0.0))
    results: list[RequestEnergy] = []  # list.append is atomic under the GIL
    stop = threading.Event()
    energy = 0.0

    def sampler():
        nonlocal energy
        while not stop.is_set():
            energy += 0.001 + 0.0005 * (energy * 1000 % 3)
            gpu = energy / 3
            attributor.on_window(_sample(energy, gpu=gpu, gpu_quality="measured"))
            _invariant(attributor)
            time.sleep(0.002)

    def requester(i: int):
        for _ in range(20):
            meter = _Meter()
            state = attributor.begin(f"GET /{i % 3}", meter)
            state.on_resolved = results.append
            meter.ns += 5_000_000
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
    resolved = [r.energy_kwh + r.gpu_kwh for r in results if r.energy_kwh is not None]
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
    attributor = EnergyAttributor(cpu_times=_all_ours())
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
    attributor = EnergyAttributor(cpu_times=_all_ours())
    attributor.reset_window(_sample(0.0, timestamp=0.0))
    state = _begin(attributor, cpu_s=1.0)  # all of the process's CPU time
    cpu, ram = _kwh(25, 2), _kwh(3, 2)
    attributor.on_window(
        _sample(cpu + ram, cpu=cpu, ram_kwh=ram, timestamp=2.0, cpu_idle_w=10.0)
    )
    assert state.energy == pytest.approx(_kwh(15, 2))
    assert attributor.idle_kwh == pytest.approx(_kwh(10 + 3, 2))
    _invariant(attributor)


def test_gpu_idle_is_estimated_separately():
    attributor = EnergyAttributor(cpu_times=_all_ours())
    gpu = dict(gpu_quality="measured")
    attributor.reset_window(_sample(0.0, timestamp=0.0, **gpu))
    attributor.on_window(_sample(_kwh(50, 1), gpu=_kwh(50, 1), timestamp=1.0, **gpu))
    attributor.on_window(
        _sample(_kwh(50 + 100, 1), gpu=_kwh(50 + 100, 1), timestamp=2.0, **gpu)
    )
    assert attributor.report()["idle_power_w"]["gpu"] == pytest.approx(50)
    assert attributor.unattributed_kwh == pytest.approx(_kwh(50, 1))
    _invariant(attributor)


def test_other_processes_keep_their_share_of_cpu_energy():
    """Fake psutil: we used 1 of the machine's 4 busy CPU seconds."""
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0))
    state = _begin(attributor, cpu_s=1.0)
    times.advance(process=1.0, busy=4.0, total=8.0)
    attributor.on_window(_sample(_kwh(40, 1), timestamp=1.0))
    assert state.energy == pytest.approx(_kwh(10, 1))
    assert attributor.other_processes_kwh == pytest.approx(_kwh(30, 1))
    _invariant(attributor)


def test_model_cost_per_cpu_second_is_charged_and_capped():
    """Charged b * cpu_seconds; the rest of the machine's energy is not ours."""
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0, cpu_w_per_busy_cpu=10.0))
    state = _begin(attributor, cpu_s=1.0)
    # 100 J above idle, 4 busy CPU-seconds, 1 of them ours: our share is 25 J,
    # but the model says one CPU-second costs 10 J.
    times.advance(process=1.0, busy=4.0, total=8.0)
    attributor.on_window(_sample(_kwh(100, 1), timestamp=1.0, cpu_w_per_busy_cpu=10.0))
    assert state.energy == pytest.approx(_kwh(10, 1))
    assert attributor.other_processes_kwh == pytest.approx(_kwh(90, 1))
    assert attributor.report()["cpu_cost_source"] == "model"
    # A cost above our share is capped at the share.
    state.meter.ns += int(1e9)
    times.advance(process=1.0, busy=4.0, total=8.0)
    attributor.on_window(_sample(_kwh(200, 1), timestamp=2.0, cpu_w_per_busy_cpu=60.0))
    assert state.energy == pytest.approx(_kwh(10 + 25, 1))
    _invariant(attributor)


def test_cost_cap_is_shared_by_requests_and_process_rest():
    """A binding cap scales metered and unmetered process CPU alike."""
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0, cpu_w_per_busy_cpu=60.0))
    state = _begin(attributor, cpu_s=0.5)
    # Our share is 25 J for 1 CPU-second; the model asks 60 J for it, so the
    # cap binds, and the meters claimed half of our CPU time.
    times.advance(process=1.0, busy=4.0, total=8.0)
    attributor.on_window(_sample(_kwh(100, 1), timestamp=1.0, cpu_w_per_busy_cpu=60.0))
    assert state.energy == pytest.approx(_kwh(12.5, 1))
    assert attributor.process_unattributed_kwh == pytest.approx(_kwh(12.5, 1))
    _invariant(attributor)


def test_fitted_cost_per_cpu_second_ignores_other_processes_load():
    """Linear machine: 5 W idle + 10 W per busy CPU. A hog doesn't move us."""
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    measured = dict(cpu_idle_w=None)
    attributor.reset_window(_sample(0.0, timestamp=0.0, **measured))
    energy = 0.0
    for t in range(1, 31):
        busy = 1.0 + (t % 4)
        times.advance(process=0.5, busy=busy, total=8.0)
        energy += _kwh(5 + 10 * busy, 1)
        attributor.on_window(_sample(energy, timestamp=float(t), **measured))
    assert attributor.report()["cpu_cost_source"] == "fit"
    state = _begin(attributor, start=30.0, cpu_s=0.5)
    times.advance(process=0.5, busy=6.0, total=8.0)  # a hog takes 5.5 CPUs
    attributor.on_window(_sample(energy + _kwh(65, 1), timestamp=31.0, **measured))
    assert state.energy == pytest.approx(_kwh(5, 1))
    assert attributor.report()["cpu_j_per_cpu_second"] == pytest.approx(10)
    _invariant(attributor)


def test_process_share_is_clamped_and_skipped_in_process_mode():
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    attributor.reset_window(_sample(0.0, timestamp=0.0))
    # Tick rounding can make our CPU time exceed the machine's busy time.
    times.advance(process=1.2, busy=1.0)
    attributor.on_window(_sample(_kwh(40, 1), timestamp=1.0))
    assert attributor.other_processes_kwh == 0.0
    # Load mode with tracking_mode="process" already measured only us.
    times.advance(process=1.0, busy=4.0)
    attributor.on_window(_sample(_kwh(80, 1), timestamp=2.0, cpu_per_process=True))
    assert attributor.other_processes_kwh == 0.0
    assert attributor.unattributed_kwh == pytest.approx(_kwh(80, 1))
    _invariant(attributor)


def test_cpu_times_busy_excludes_idle_and_steal(monkeypatch):
    from collections import namedtuple

    from codecarbon.integrations.fastapi import attribution

    Times = namedtuple("Times", "user nice system idle iowait steal guest guest_nice")
    monkeypatch.setattr(
        attribution.psutil, "cpu_times", lambda: Times(5, 1, 2, 10, 3, 4, 2, 1)
    )
    _, busy, total = attribution._cpu_times()
    assert (busy, total) == (8, 25)


def _burn(seconds: float) -> None:
    end = time.thread_time_ns() + int(seconds * 1e9)
    while time.thread_time_ns() < end:
        pass


def test_metered_returns_and_counts_only_cpu_time():
    async def work():
        _burn(0.01)
        await asyncio.sleep(0.05)
        _burn(0.01)
        return 42

    async def main():
        return await _Metered(work(), meter)

    meter = _Meter()
    assert asyncio.run(main()) == 42
    assert 0.02 <= meter.ns / 1e9 < 0.03


def test_metered_propagates_errors_and_cancellation():
    meter = _Meter()

    async def boom():
        await asyncio.sleep(0)
        raise ValueError("boom")

    async def main():
        await _Metered(boom(), meter)

    with pytest.raises(ValueError):
        asyncio.run(main())

    cleaned = []

    async def slow():
        try:
            await asyncio.sleep(10)
        finally:
            cleaned.append(True)

    async def cancel_it():
        task = asyncio.ensure_future(_Metered(slow(), meter))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel_it())
    assert cleaned == [True]


def test_metered_passes_thrown_exceptions_the_coroutine_handles():
    async def swallow():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return "handled"

    async def main():
        task = asyncio.ensure_future(_Metered(swallow(), _Meter()))
        await asyncio.sleep(0.01)
        task.cancel()
        return await task

    assert asyncio.run(main()) == "handled"


def test_metered_drives_any_awaitable():
    """ASGI only promises an awaitable: a Future or custom ``__await__`` works."""

    class Custom:
        def __await__(self):
            yield from asyncio.sleep(0).__await__()
            return "custom"

    async def main():
        future = asyncio.get_running_loop().create_future()
        asyncio.get_running_loop().call_soon(future.set_result, 7)
        return await _Metered(future, _Meter()), await _Metered(Custom(), _Meter())

    assert asyncio.run(main()) == (7, "custom")


def test_metered_close_closes_the_inner_coroutine():
    closed = []

    @types.coroutine
    def pause():
        yield

    async def inner():
        try:
            await pause()
        finally:
            closed.append(True)

    async def outer():
        await _Metered(inner(), _Meter())

    coro = outer()
    coro.send(None)  # suspended inside pause()
    coro.close()
    assert closed == [True]


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
        # Per-process energy: the real machine's other processes don't matter.
        return _sample(self._total_energy.kWh, cpu_per_process=True)

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
    # A sync endpoint's work runs in a worker thread the meter doesn't see.
    assert 0.0 <= energy.energy_kwh < 1.0
    assert energy.cpu_seconds > 0
    assert kg == pytest.approx(energy.energy_kwh * 0.5)


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
    assert sample.cpu_w_per_busy_cpu == pytest.approx(
        0.9 * cpu._tdp * tracker._pue / psutil.cpu_count()
    )
    parts = sample.cpu_kwh + sample.gpu_kwh + sample.ram_kwh
    assert sample.total_kwh == pytest.approx(parts)
    assert sample.total_kwh > 0


def test_window_sample_error_never_breaks_measurement(monkeypatch):
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=3600,
        output_methods=[],
        allow_multiple_runs=True,
        force_mode_cpu_load=True,
    )
    samples = []
    tracker.add_energy_window_observer(samples.append)

    def broken():
        raise RuntimeError("sample")

    monkeypatch.setattr(tracker, "_window_sample", broken)
    tracker.start()
    try:
        tracker._measure_power_and_energy()
        assert tracker._total_energy.kWh > 0
    finally:
        tracker.stop()
    assert samples == []


def test_conservation_with_fake_clocks_and_energy():
    """Random windows, meters and GPU load: nothing is created or lost."""
    import random

    rng = random.Random(1428)
    times = _FakeTimes()
    attributor = EnergyAttributor(cpu_times=times)
    gpu = dict(gpu_quality="measured", cpu_idle_w=None)
    totals = dict(cpu=0.0, gpu=0.0, ram=0.0)
    attributor.reset_window(_sample(0.0, timestamp=0.0, **gpu))
    results = []
    live = []
    for t in range(1, 500):
        for _ in range(rng.randint(0, 4)):
            state = _begin(attributor, start=t - rng.random())
            state.on_resolved = results.append
            live.append(state)
        for state in live:
            state.meter.ns += rng.randint(0, 50_000_000)
        for state in rng.sample(live, k=len(live) // 2):
            attributor.end(state)
            live.remove(state)
        for part, watts in (("cpu", 80), ("gpu", 250), ("ram", 5)):
            totals[part] += _kwh(watts * rng.random(), 1)
        times.advance(process=rng.random(), busy=rng.random() * 4, total=8.0)
        attributor.on_window(
            _sample(
                sum(totals.values()),
                cpu=totals["cpu"],
                gpu=totals["gpu"],
                ram_kwh=totals["ram"],
                timestamp=float(t),
                **gpu,
            )
        )
        _invariant(attributor)
    attributor.close()
    report = attributor.report()
    assert report["settled_kwh"] == pytest.approx(sum(totals.values()), rel=1e-12)
    charged = sum(r.energy_kwh + r.gpu_kwh for r in results if r.windows)
    assert charged == pytest.approx(report["attributed_kwh"], rel=1e-12)
    assert all(report[k] > 0 for k in ("idle_kwh", "other_processes_kwh"))


def _metered_app(seen):
    app = FastAPI()
    app.add_middleware(
        CodeCarbonMiddleware,
        tracker=_FakeTracker(),
        on_request=lambda energy, kg, status: seen.append(energy),
    )

    @app.get("/burn/{ms}")
    async def burn(ms: float):
        _burn(ms / 1000)
        return {}

    @app.get("/burn-sync/{ms}")
    def burn_sync(ms: float):
        _burn(ms / 1000)
        return {}

    @app.get("/sleep/{ms}")
    async def sleep(ms: float):
        await asyncio.sleep(ms / 1000)
        return {}

    return app


def _cpu_seconds(path: str, repeat: int = 5) -> list[float]:
    seen = []
    with TestClient(_metered_app(seen)) as client:
        client.get(path)  # warm-up: first-call imports and caches
        for _ in range(repeat):
            assert client.get(path).status_code == 200
    # Lifespan shutdown closed the middleware and emitted everything.
    return [energy.cpu_seconds for energy in seen[1:]]


def test_cpu_seconds_of_a_known_async_burn():
    for cpu_s in _cpu_seconds("/burn/20"):
        assert cpu_s == pytest.approx(0.020, rel=0.10, abs=0.0002)


def test_cpu_seconds_of_a_known_sync_burn():
    for cpu_s in _cpu_seconds("/burn-sync/20"):
        assert cpu_s == pytest.approx(0.020, rel=0.10, abs=0.0002)


def _threadpool_app(seen, **middleware):
    """Every way FastAPI and Starlette send a request's work to a thread."""
    from fastapi import APIRouter, Depends
    from fastapi.responses import StreamingResponse

    app = FastAPI()
    app.add_middleware(
        CodeCarbonMiddleware,
        tracker=_FakeTracker(),
        on_request=lambda energy, kg, status: seen.append(energy),
        **middleware,
    )

    def burn_dep() -> int:
        _burn(0.010)
        return 1

    def real_value() -> str:
        return "real"

    @app.get("/sync-dep")
    async def sync_dep(x: int = Depends(burn_dep)):
        return {}

    @app.get("/stream")
    def stream():
        def chunks():
            for _ in range(4):
                _burn(0.005)
                yield b"x"

        return StreamingResponse(chunks())

    router = APIRouter()

    @router.get("/sync")
    def included_sync():
        _burn(0.010)
        return {}

    app.include_router(router, prefix="/included")

    @app.get("/value")
    def value(v: str = Depends(real_value)):
        return {"v": v}

    app.state.real_value = real_value
    return app


@pytest.mark.parametrize(
    "path, cpu_s",
    [("/sync-dep", 0.010), ("/stream", 0.020), ("/included/sync", 0.010)],
)
def test_threadpool_work_is_metered(path, cpu_s):
    seen = []
    with TestClient(_threadpool_app(seen)) as client:
        client.get(path)  # warm-up
        for _ in range(3):
            assert client.get(path).status_code == 200
    for energy in seen[1:]:
        assert energy.cpu_seconds == pytest.approx(cpu_s, rel=0.10, abs=0.0005)


def test_plain_starlette_sync_endpoint_is_metered():
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    def endpoint(request):
        _burn(0.010)
        return PlainTextResponse("ok")

    seen = []
    app = Starlette(
        routes=[Route("/", endpoint)],
        middleware=[
            Middleware(
                CodeCarbonMiddleware,
                tracker=_FakeTracker(),
                on_request=lambda energy, kg, status: seen.append(energy),
            )
        ],
    )
    with TestClient(app) as client:
        for _ in range(3):
            assert client.get("/").status_code == 200
    for energy in seen:
        assert energy.cpu_seconds == pytest.approx(0.010, rel=0.10, abs=0.0005)


def test_dependency_overrides_still_work():
    seen = []
    app = _threadpool_app(seen)
    app.dependency_overrides[app.state.real_value] = lambda: "override"
    with TestClient(app) as client:
        assert client.get("/value").json() == {"v": "override"}


def test_threadpool_metering_can_be_turned_off():
    import anyio.to_thread

    original = anyio.to_thread.run_sync
    seen = []
    with TestClient(_threadpool_app(seen, meter_threadpool=False)) as client:
        client.get("/included/sync")
        assert anyio.to_thread.run_sync is original
    assert seen[0].cpu_seconds < 0.005


def test_run_sync_patch_is_transparent_and_restored():
    import anyio
    import anyio.to_thread

    from codecarbon.integrations.fastapi import middleware as mw

    original = anyio.to_thread.run_sync
    limiter = anyio.CapacityLimiter(1)

    def add(a, b):
        return a + b

    def boom():
        raise ValueError("boom")

    async def main():
        # No request meter set: plain pass-through, arguments and errors.
        assert await anyio.to_thread.run_sync(add, 1, 2, limiter=limiter) == 3
        with pytest.raises(ValueError):
            await anyio.to_thread.run_sync(boom)
        meter = _Meter()
        token = mw._current_meter.set(meter)
        try:
            await anyio.to_thread.run_sync(_burn, 0.005)
        finally:
            mw._current_meter.reset(token)
        return meter

    mw._patch_run_sync()
    mw._patch_run_sync()  # idempotent: one wrapper, two users
    try:
        assert anyio.to_thread.run_sync is mw._metered_run_sync
        meter = anyio.run(main)
        assert meter.total_ns() / 1e9 == pytest.approx(0.005, rel=0.2)
        mw._unpatch_run_sync()
        assert anyio.to_thread.run_sync is mw._metered_run_sync
    finally:
        mw._unpatch_run_sync()
    assert anyio.to_thread.run_sync is original


def test_threadpool_patch_restored_on_shutdown():
    import anyio.to_thread

    original = anyio.to_thread.run_sync
    with TestClient(_threadpool_app([])) as client:
        client.get("/included/sync")
        assert anyio.to_thread.run_sync is not original
    assert anyio.to_thread.run_sync is original


@pytest.mark.skipif(
    not hasattr(time, "pthread_getcpuclockid"),
    reason="no way to read another thread's CPU clock on this platform",
)
def test_long_sync_call_is_charged_while_running():
    meter = _Meter()
    started = threading.Event()

    def work():
        started.set()
        _burn(0.2)

    worker = threading.Thread(target=meter.run_in_thread, args=(work,))
    worker.start()
    started.wait()
    time.sleep(0.1)
    midway = meter.total_ns()
    worker.join()
    assert 0.02 < midway / 1e9 < 0.2
    assert meter.total_ns() / 1e9 == pytest.approx(0.2, rel=0.1)


def test_sleeping_endpoint_uses_almost_no_cpu():
    for cpu_s in _cpu_seconds("/sleep/50"):
        assert cpu_s < 0.002
