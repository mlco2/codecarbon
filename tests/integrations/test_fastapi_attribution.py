"""Per-request energy attribution.

Every test here injects a known constant power and a deterministic clock, so
the numbers are identical on Apple Silicon and on a 280 W Linux box. Nothing
in this file reads real hardware.
"""

from __future__ import annotations

import asyncio
import math
import time
from types import SimpleNamespace

import pytest

from codecarbon.integrations.fastapi.attribution import (
    INTERPOLATED,
    MEASURED,
    UNRESOLVED,
    EnergyAttributor,
    _TimedCoro,
    install_cpu_accounting,
)

WATTS = 100.0


class FakeClock:
    """Monotonic clock we drive by hand, plus the energy it implies."""

    def __init__(self, watts: float = WATTS) -> None:
        self.now = 1000.0
        self.energy_kwh = 0.0
        self.watts = watts

    def advance(self, dt: float) -> float:
        self.now += dt
        self.energy_kwh += self.watts * dt / 3.6e6
        return self.energy_kwh


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(
        "codecarbon.integrations.fastapi.attribution.time.perf_counter", lambda: c.now
    )
    return c


def make(clock, **kwargs) -> EnergyAttributor:
    a = EnergyAttributor(**kwargs)
    a.reset_window(clock.energy_kwh)
    return a


# --- the headline invariant --------------------------------------------------


@pytest.mark.parametrize("concurrency", [1, 4, 8, 32, 100])
def test_shares_plus_unattributed_equal_the_run_total(clock, concurrency):
    """sum(per-request) + unattributed == run total, exactly, at every window.

    The old start/stop-snapshot path returns ``concurrency`` times the run
    total here (3.55x at 4, 7.14x at 8, 28.5x at 32, 88.5x at 100).
    """
    emitted = []
    a = make(clock, on_request=emitted.append)

    clock.advance(0.5)  # idle head
    a.on_window(clock.energy_kwh)

    # staggered starts, staggered ends, windows closing throughout
    states = []
    for i in range(concurrency):
        states.append(a.begin(f"GET /r{i}"))
        clock.advance(0.03)
        if i % 3 == 0:
            a.on_window(clock.energy_kwh)
    for i, state in enumerate(states):
        clock.advance(0.03)
        a.end(state)
        if i % 2 == 0:
            a.on_window(clock.energy_kwh)
            # invariant holds after every single window, not just at the end
            assert math.isclose(
                a.attributed_kwh + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12
            )

    clock.advance(0.5)  # idle tail flushes the stragglers
    a.on_window(clock.energy_kwh)
    a.close()

    assert len(emitted) == concurrency
    per_request = sum(r.energy_kwh or 0.0 for r in emitted)
    assert math.isclose(per_request, a.attributed_kwh, rel_tol=1e-12)
    assert math.isclose(per_request + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12)
    # the last partial window is never settled, so settled <= run total
    assert a.settled_kwh <= clock.energy_kwh
    assert per_request / clock.energy_kwh <= 1.0


def test_equal_overlap_splits_evenly_and_idle_stays_unattributed(clock):
    a = make(clock)
    r1 = a.begin("GET /a")
    clock.advance(0.5)
    a.on_window(clock.energy_kwh)  # r1 alone for 0.5 s
    r2 = a.begin("GET /b")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)  # shared 1.0 s
    a.end(r1)
    clock.advance(0.5)
    a.on_window(clock.energy_kwh)  # r2 alone for 0.5 s
    a.end(r2)
    clock.advance(0.5)  # idle
    a.on_window(clock.energy_kwh)

    # each got 0.5 s alone + half of 1.0 s shared == 1.0 s of machine
    one_second = WATTS * 1.0 / 3.6e6
    assert r1.energy == pytest.approx(one_second)
    assert r2.energy == pytest.approx(one_second)
    assert a.unattributed_kwh == pytest.approx(WATTS * 0.5 / 3.6e6)


def test_zero_width_window_is_ignored(clock):
    """Two samples at the same instant must not divide by a zero-width window."""
    a = make(clock)
    a.begin("GET /a")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    settled = a.settled_kwh
    a.on_window(clock.energy_kwh + 1.0)  # same timestamp, energy jumped
    assert a.windows_settled == 1
    assert a.settled_kwh == settled  # the jump is not banked, nothing shared


def test_window_with_nothing_in_flight_is_unattributed(clock):
    a = make(clock)
    clock.advance(2.0)
    a.on_window(clock.energy_kwh)
    assert a.attributed_kwh == 0.0
    assert a.unattributed_kwh == pytest.approx(WATTS * 2.0 / 3.6e6)


def test_energy_counter_going_backwards_is_skipped_not_negative(clock):
    a = make(clock)
    state = a.begin("GET /a")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    before = a.attributed_kwh
    clock.advance(1.0)
    a.on_window(0.0)  # RAPL wrap: cumulative total dropped
    a.end(state)
    assert a.windows_skipped == 1
    assert a.attributed_kwh == before  # nothing negative handed out
    assert math.isclose(
        a.attributed_kwh + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12
    )


# --- deferred finalisation ---------------------------------------------------


def test_end_does_not_settle_and_the_next_window_pays_out(clock):
    emitted = []
    a = make(clock, on_request=emitted.append)
    state = a.begin("GET /a")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    clock.advance(0.5)
    a.end(state)
    assert emitted == []  # nothing settled at response time
    energy_at_end = state.energy
    clock.advance(0.1)
    a.on_window(clock.energy_kwh)  # the window covering the tail closes
    assert len(emitted) == 1
    assert emitted[0].energy_kwh > energy_at_end
    assert math.isclose(
        a.attributed_kwh + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12
    )


# --- quality tiers -----------------------------------------------------------


def test_quality_tiers(clock):
    emitted = []
    a = make(clock, on_request=emitted.append)

    never = a.begin("GET /never")  # zero measurable overlap with any window
    a.end(never)

    short = a.begin("GET /short")
    clock.advance(0.01)
    a.end(short)
    clock.advance(0.01)
    a.on_window(clock.energy_kwh)  # covers /short's single boundary; /never got 0 s

    long_req = a.begin("GET /long")
    for _ in range(3):
        clock.advance(0.5)
        a.on_window(clock.energy_kwh)
    a.end(long_req)
    clock.advance(0.1)
    a.on_window(clock.energy_kwh)

    by_endpoint = {r.endpoint: r for r in emitted}
    assert by_endpoint["GET /never"].quality == UNRESOLVED
    assert by_endpoint["GET /never"].energy_kwh is None  # zero would be a lie
    assert by_endpoint["GET /short"].quality == INTERPOLATED
    assert by_endpoint["GET /short"].energy_kwh > 0
    assert by_endpoint["GET /long"].quality == MEASURED
    assert by_endpoint["GET /long"].windows >= 2


def test_uncertainty_payload_travels_with_every_number(clock):
    emitted = []
    a = make(clock, on_request=emitted.append)
    a.begin("GET /a")
    state = a.begin("GET /b")
    for _ in range(2):
        clock.advance(0.5)
        a.on_window(clock.energy_kwh)
    a.end(state)
    clock.advance(0.1)
    a.on_window(clock.energy_kwh)

    payload = emitted[0].to_dict()
    # /b ended exactly on a window boundary, so the following window gave it
    # zero overlap and did not count towards its coverage.
    assert payload["windows"] == 2
    assert payload["mean_concurrency"] == pytest.approx(2.0)
    assert payload["weighting"] == "wall"
    assert payload["baseline_subtracted"] is False
    assert payload["quality"] == MEASURED
    assert payload["cpu_seconds"] == 0.0
    assert "error" not in payload  # no synthesised +/- bar


# --- baseline ----------------------------------------------------------------


def test_baseline_is_none_when_the_server_never_idles(clock):
    a = make(clock, subtract_baseline=True)
    a.begin("GET /a")
    for _ in range(4):
        clock.advance(0.5)
        a.on_window(clock.energy_kwh)
    assert a.baseline_watts() is None
    # nothing guessed from nameplate TDP, nothing subtracted
    assert a.unattributed_kwh == 0.0
    assert math.isclose(a.attributed_kwh, a.settled_kwh, rel_tol=1e-12)


def test_baseline_is_measured_from_idle_windows_and_reported_separately(clock):
    emitted = []
    a = make(clock, subtract_baseline=True, on_request=emitted.append)
    for _ in range(3):  # idle: establishes P_idle == 100 W
        clock.advance(1.0)
        a.on_window(clock.energy_kwh)
    assert a.baseline_watts() == pytest.approx(WATTS)

    clock.watts = 300.0  # 100 W idle + 200 W of work
    state = a.begin("GET /a")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    a.end(state)
    clock.watts = WATTS
    clock.advance(0.01)
    a.on_window(clock.energy_kwh)

    result = emitted[0]
    assert result.baseline_subtracted is True
    # marginal energy is the 200 W above idle; baseline is reported apart
    assert result.energy_kwh == pytest.approx(200.0 * 1.0 / 3.6e6, rel=1e-3)
    assert result.baseline_share_kwh == pytest.approx(WATTS * 1.0 / 3.6e6, rel=1e-3)
    assert math.isclose(
        a.attributed_kwh + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12
    )


def test_baseline_never_drives_a_share_negative(clock):
    """A window drawing less than the measured baseline clamps, not inverts."""
    a = make(clock, subtract_baseline=True)
    for _ in range(3):
        clock.advance(1.0)
        a.on_window(clock.energy_kwh)
    clock.watts = 10.0  # below the 100 W baseline
    state = a.begin("GET /a")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    assert state.energy == 0.0
    assert state.energy >= 0.0


# --- cpu weighting -----------------------------------------------------------


def test_cpu_weighting_splits_by_cpu_time_not_wall_time(clock):
    a = make(clock, weighting="cpu")
    busy = a.begin("GET /cpu")
    idle = a.begin("GET /io")
    busy.cpu_acc[0] = 0.4  # 0.4 CPU-seconds burned
    idle.cpu_acc[0] = 0.0  # slept the whole window
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    assert idle.energy == 0.0
    assert busy.energy > 0
    # normalised by capacity (1.0 s * 1 core), NOT by observed CPU: the busy
    # request gets 40% of the window, the unclaimed 60% stays unattributed.
    assert busy.energy == pytest.approx(0.4 * clock.energy_kwh)
    assert math.isclose(
        a.attributed_kwh + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12
    )


def test_cpu_weighting_capacity_scales_with_cores(clock):
    a = make(clock, weighting="cpu", cores=4)
    state = a.begin("GET /cpu")
    state.cpu_acc[0] = 0.4
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    # same 0.4 CPU-s against 4.0 CPU-s of capacity
    assert state.energy == pytest.approx(0.1 * clock.energy_kwh)


def test_cpu_window_with_no_one_on_cpu_is_idle_energy(clock):
    a = make(clock, weighting="cpu")
    state = a.begin("GET /io")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    assert state.energy == 0.0
    assert a.unattributed_kwh == pytest.approx(clock.energy_kwh)
    assert a.baseline_watts() == pytest.approx(WATTS)


def test_cpu_accounting_charges_real_cpu_time_to_the_owning_request():
    """The task factory must bill a task's resumptions to the request in context."""
    a = EnergyAttributor(weighting="cpu")

    async def drive():
        install_cpu_accounting(asyncio.get_running_loop())
        busy = a.begin("GET /busy")
        await asyncio.create_task(_burn(0.02))
        sleeper = a.begin("GET /sleep")
        await asyncio.create_task(asyncio.sleep(0.01))
        cancelled = asyncio.create_task(asyncio.sleep(10))
        await asyncio.sleep(0)
        cancelled.cancel()  # drives _TimedCoro.throw
        with pytest.raises(asyncio.CancelledError):
            await cancelled
        return busy, sleeper

    busy, sleeper = asyncio.run(drive())
    assert busy.cpu_acc[0] > 0
    # the sleeper's own task burned near-zero CPU compared with the burner
    assert sleeper.cpu_acc[0] < busy.cpu_acc[0]
    a.close()  # weighting == "cpu": also clears the context var


def _burn(seconds: float):
    async def inner():
        deadline = time.thread_time() + seconds
        while time.thread_time() < deadline:
            pass

    return inner()


def test_timed_coro_delegates_close_await_and_attributes():
    acc = [0.0]

    async def coro():
        return 42

    wrapped = _TimedCoro(coro(), acc)
    assert wrapped.cr_await is None  # __getattr__ delegates
    assert wrapped.__await__() is not None
    wrapped.close()


def test_rejects_bad_configuration():
    with pytest.raises(ValueError):
        EnergyAttributor(weighting="vibes")
    with pytest.raises(ValueError):
        EnergyAttributor(cores=0)


# --- aggregates and bounded state --------------------------------------------


def test_endpoint_aggregate_is_the_primary_output(clock):
    a = make(clock)
    for _ in range(10):
        state = a.begin("GET /items/{id}")
        clock.advance(0.05)
        a.end(state)
        clock.advance(0.05)
        a.on_window(clock.energy_kwh)
    clock.advance(0.1)
    a.on_window(clock.energy_kwh)
    a.close()

    report = a.report()
    agg = report["endpoints"]["GET /items/{id}"]
    assert agg["count"] == 10
    assert agg["mean_energy_kwh"] == pytest.approx(agg["energy_kwh"] / 10)
    assert sum(agg["quality"].values()) == 10
    assert math.isclose(report["total_kwh"], report["settled_kwh"], rel_tol=1e-12)


def test_in_flight_map_is_flat_after_10000_requests(clock):
    a = make(clock)
    for _ in range(10_000):
        state = a.begin("GET /x")
        clock.advance(0.0005)
        a.end(state)
        a.on_window(clock.energy_kwh)
        assert len(a._in_flight) <= 1
    assert len(a._in_flight) == 0
    assert len(a.endpoints) == 1  # aggregates are bounded by route count
    assert len(a._idle_power_w) <= 256  # idle samples are a bounded deque
    assert math.isclose(
        a.attributed_kwh + a.unattributed_kwh, a.settled_kwh, rel_tol=1e-12
    )


def test_close_emits_unresolved_requests_still_in_flight(clock):
    emitted = []
    a = make(clock, on_request=emitted.append)
    a.begin("GET /hanging")
    a.close()
    assert len(emitted) == 1
    assert emitted[0].quality == UNRESOLVED
    assert emitted[0].energy_kwh is None
    assert len(a._in_flight) == 0


def test_callback_failure_does_not_break_attribution(clock):
    def boom(_result):
        raise RuntimeError("user callback")

    a = make(clock, on_request=boom)
    state = a.begin("GET /a")
    clock.advance(1.0)
    a.on_window(clock.energy_kwh)
    a.end(state)
    clock.advance(0.1)
    a.on_window(clock.energy_kwh)  # must not raise
    assert len(a._in_flight) == 0


# --- middleware wiring -------------------------------------------------------


def test_middleware_rejects_headers_with_attribution():
    from codecarbon.integrations.fastapi.middleware import CodeCarbonMiddleware

    with pytest.raises(ValueError, match="response_headers"):
        CodeCarbonMiddleware(None, attribution=True, response_headers=True)


def test_middleware_end_to_end_against_a_fake_tracker():
    """Real ASGI app + real middleware, injected power, no hardware read."""
    import httpx
    from fastapi import FastAPI

    from codecarbon import OfflineEmissionsTracker
    from codecarbon.integrations.fastapi.middleware import add_codecarbon_middleware

    app = FastAPI()

    @app.get("/work")
    async def work():
        await asyncio.sleep(0.3)
        return {"ok": True}

    emitted = []
    attributor = EnergyAttributor(on_request=emitted.append)
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=0.1,
        force_cpu_power=100,
        force_ram_power=10,
        save_to_file=False,
        allow_multiple_runs=True,
        log_level="error",
    )
    app.state.codecarbon_tracker = tracker
    add_codecarbon_middleware(app, attribution=attributor)

    async def drive():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t"
        ) as client:
            responses = await asyncio.gather(*(client.get("/work") for _ in range(4)))
        assert all(r.status_code == 200 for r in responses)
        await asyncio.sleep(0.3)

    tracker.start()
    try:
        asyncio.run(drive())
    finally:
        tracker.stop()
        attributor.close()

    # app.state only names the middleware once Starlette has built the stack.
    middleware = app.state.codecarbon_middleware
    total = tracker.final_emissions_data.energy_consumed
    assert len(emitted) == 4
    per_request = sum(r.energy_kwh or 0.0 for r in emitted)
    # the whole point: four concurrent requests do not each own the run total
    assert per_request <= total * 1.001
    assert per_request > 0
    report = middleware.attribution_report()
    assert report["endpoints"]["GET /work"]["count"] == 4
    assert report["total_kwh"] == pytest.approx(report["settled_kwh"])
    assert report["in_flight"] == 0


def test_attribution_path_takes_no_out_of_band_hardware_samples():
    """The request path must not force ``_maybe_measure_power_and_energy``."""
    import httpx
    from fastapi import FastAPI

    from codecarbon import OfflineEmissionsTracker
    from codecarbon.integrations.fastapi.middleware import add_codecarbon_middleware

    app = FastAPI()

    @app.get("/ping")
    async def ping():
        return {}

    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=60,
        force_cpu_power=100,
        force_ram_power=10,
        save_to_file=False,
        allow_multiple_runs=True,
        log_level="error",
    )
    calls = []
    tracker._maybe_measure_power_and_energy = lambda: calls.append(1)
    app.state.codecarbon_tracker = tracker
    add_codecarbon_middleware(app, attribution=True)

    async def drive():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t"
        ) as client:
            for _ in range(20):
                assert (await client.get("/ping")).status_code == 200

    tracker.start()
    try:
        asyncio.run(drive())
    finally:
        tracker.stop()
        app.state.codecarbon_middleware.attributor.close()
    assert calls == []


def test_tracker_observer_is_removable_and_survives_a_raising_callback():
    """The tracker must not let one bad observer break a sampling window."""
    from codecarbon import OfflineEmissionsTracker

    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        save_to_file=False,
        allow_multiple_runs=True,
        log_level="error",
    )
    seen = []

    def boom(_kwh):
        raise RuntimeError("bad observer")

    tracker.add_energy_window_observer(boom)
    tracker.add_energy_window_observer(seen.append)
    tracker._notify_energy_window_observers()  # must not raise
    assert len(seen) == 1

    tracker.remove_energy_window_observer(boom)
    tracker.remove_energy_window_observer(boom)  # idempotent
    tracker._notify_energy_window_observers()
    assert len(seen) == 2
    assert tracker._window_observers == [seen.append]


def test_shutdown_unhooks_the_observer_and_flushes_in_flight_requests():
    """shutdown_codecarbon_middleware must detach from the tracker and emit."""
    from fastapi import FastAPI

    from codecarbon import OfflineEmissionsTracker
    from codecarbon.integrations.fastapi.middleware import (
        CodeCarbonMiddleware,
        shutdown_codecarbon_middleware,
    )

    app = FastAPI()
    emitted = []
    attributor = EnergyAttributor(on_request=emitted.append)
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=0.1,
        force_cpu_power=100,
        force_ram_power=10,
        save_to_file=False,
        allow_multiple_runs=True,
        log_level="error",
    )
    app.state.codecarbon_tracker = tracker
    # No request is served here, so build the middleware and register it the way
    # add_codecarbon_middleware would once Starlette builds the stack.
    middleware = CodeCarbonMiddleware(app, attribution=attributor)
    app.state.codecarbon_middleware = middleware

    tracker.start()
    try:

        middleware._bind_attributor(SimpleNamespace(app=app))
        assert attributor.on_window in tracker._window_observers
        attributor.begin("GET /hanging")
    finally:
        tracker.stop()
        shutdown_codecarbon_middleware(app)

    assert attributor.on_window not in tracker._window_observers
    assert middleware._attribution_tracker is None
    assert len(emitted) == 1  # the in-flight request was flushed by close()


def test_cpu_weighting_end_to_end_installs_the_task_factory():
    """weighting="cpu" through the middleware: factory installed, CPU billed."""
    import httpx
    from fastapi import FastAPI

    from codecarbon import OfflineEmissionsTracker
    from codecarbon.integrations.fastapi.middleware import add_codecarbon_middleware

    app = FastAPI()

    @app.get("/burn")
    async def burn():
        deadline = time.thread_time() + 0.05
        while time.thread_time() < deadline:
            pass
        return {}

    emitted = []
    attributor = EnergyAttributor(weighting="cpu", on_request=emitted.append)
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=0.1,
        force_cpu_power=100,
        force_ram_power=10,
        save_to_file=False,
        allow_multiple_runs=True,
        log_level="error",
    )
    app.state.codecarbon_tracker = tracker
    add_codecarbon_middleware(app, attribution=attributor)
    middleware = app.state.codecarbon_middleware

    async def drive():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t"
        ) as client:
            assert (await client.get("/burn")).status_code == 200
        assert asyncio.get_running_loop().get_task_factory() is not None
        await asyncio.sleep(0.3)

    tracker.start()
    try:
        asyncio.run(drive())
    finally:
        tracker.stop()
        middleware.attributor.close()

    # exactly one observer: a rebuilt middleware stack must not double-count
    assert tracker._window_observers.count(attributor.on_window) == 1
    assert len(emitted) == 1
    assert emitted[0].weighting == "cpu"
    assert emitted[0].cpu_seconds > 0  # real on-thread CPU was billed
