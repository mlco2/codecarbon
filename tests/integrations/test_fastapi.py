"""Tests for the FastAPI per-request energy attribution."""

import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from codecarbon.emissions_tracker import EmissionsTracker
from codecarbon.integrations.fastapi import (
    EnergyAttributor,
    RequestEnergy,
    add_codecarbon_middleware,
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


def test_end_to_end_through_a_real_tracker():
    tracker = EmissionsTracker(
        measure_power_secs=0.5, output_methods=[], allow_multiple_runs=True
    )
    tracker.start()
    seen: list[tuple] = []
    app = FastAPI()
    add_codecarbon_middleware(
        app,
        tracker=tracker,
        on_request=lambda energy, emissions, status: seen.append(
            (energy, emissions, status)
        ),
    )

    @app.get("/work/{n}")
    def work(n: int):
        time.sleep(0.6)  # long enough to span a sampling window
        return {"n": n}

    try:
        with TestClient(app) as client:
            assert client.get("/work/1").status_code == 200
            time.sleep(1.2)  # let a window close and resolve the request
    finally:
        tracker.stop()
        app.state.codecarbon_middleware.close()

    assert seen, "no request was reported"
    energy, emissions, status = seen[0]
    assert status == 200
    assert energy.endpoint == "GET /work/{n}"
    assert energy.energy_kwh is not None and energy.energy_kwh > 0
    assert emissions.energy_consumed == energy.energy_kwh
    assert emissions.duration == pytest.approx(energy.duration_s)
