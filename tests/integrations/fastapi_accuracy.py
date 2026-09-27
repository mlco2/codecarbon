"""Bare-metal accuracy checks for the FastAPI per-request attribution.

Opt-in, and only meaningful on Linux with readable RAPL counters; skips
otherwise. Takes about a minute and a half::

    uv run pytest tests/integrations/fastapi_accuracy.py -m accuracy -s

The app and the load generator share one process and one event loop, so no
server dependency is needed. The client's CPU time is outside every request's
meter: it lands in ``process_unattributed_kwh`` and does not bias the
per-request numbers. The CPU hog runs in separate processes.
"""

import asyncio
import multiprocessing
import statistics
import time
from collections import defaultdict

import pytest

from codecarbon.core.cpu import is_rapl_available
from codecarbon.core.util import is_linux_os

pytestmark = [
    pytest.mark.accuracy,
    pytest.mark.skipif(
        not (is_linux_os() and is_rapl_available()), reason="needs readable RAPL"
    ),
]

CONCURRENCY = 16
PHASE_S = 30.0
ROUTES = ("/burn1", "/burn2", "/burn4", "/sleep4")


def _burn(seconds: float) -> None:
    end = time.thread_time_ns() + int(seconds * 1e9)
    while time.thread_time_ns() < end:
        pass


def _hog(stop) -> None:
    while not stop.is_set():
        _burn(0.01)


def _app():
    from fastapi import FastAPI

    from codecarbon.integrations.fastapi import CodeCarbonMiddleware

    seen = defaultdict(list)
    app = FastAPI()

    def record(energy, kg, status):
        if energy.energy_kwh is not None:
            seen[energy.endpoint.split()[-1]].append(energy.energy_kwh)

    app.add_middleware(CodeCarbonMiddleware, on_request=record)

    for ms in (1, 2, 4):

        async def burn(ms=ms):
            _burn(ms / 1000)
            return {}

        app.get(f"/burn{ms}")(burn)

    @app.get("/sleep4")
    async def sleep():
        await asyncio.sleep(0.004)
        return {}

    return app, seen


async def _load(app, seconds: float) -> None:
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        deadline = time.monotonic() + seconds

        async def worker(n: int) -> None:
            while time.monotonic() < deadline:
                assert (await client.get(ROUTES[n % len(ROUTES)])).status_code == 200
                n += 1

        await asyncio.gather(*(worker(i) for i in range(CONCURRENCY)))


def _phase(hog_processes: int = 0) -> dict[str, float]:
    """Mean per-request energy per route, kWh."""
    from codecarbon.emissions_tracker import OfflineEmissionsTracker

    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=1,
        output_methods=[],
        allow_multiple_runs=True,
    )
    tracker.start()
    if tracker._window_sample().cpu_quality != "measured":
        tracker.stop()
        pytest.skip("the tracker did not pick a measured CPU source")
    stop = multiprocessing.Event()
    hogs = [
        multiprocessing.Process(target=_hog, args=(stop,)) for _ in range(hog_processes)
    ]
    for hog in hogs:
        hog.start()
    app, seen = _app()
    app.state.codecarbon_tracker = tracker
    try:
        asyncio.run(_load(app, PHASE_S))
        time.sleep(2.5)  # let the last requests resolve on real windows
    finally:
        stop.set()
        for hog in hogs:
            hog.join()
        tracker.stop()
    means = {route: statistics.fmean(values) for route, values in seen.items()}
    print(f"\nhogs={hog_processes}", {k: f"{v:.3e} kWh" for k, v in means.items()})
    return means


@pytest.fixture(scope="module")
def quiet():
    return _phase()


def test_energy_follows_cpu_time_1_2_4(quiet):
    one = quiet["/burn1"]
    assert quiet["/burn2"] / one == pytest.approx(2, rel=0.10)
    assert quiet["/burn4"] / one == pytest.approx(4, rel=0.10)


def test_sleep_costs_at_most_2_percent_of_a_4ms_burn(quiet):
    assert quiet["/sleep4"] <= 0.02 * quiet["/burn4"]


def test_cpu_hog_changes_per_request_energy_at_most_15_percent(quiet):
    hogged = _phase(hog_processes=max(multiprocessing.cpu_count() // 2, 1))
    assert hogged["/burn4"] == pytest.approx(quiet["/burn4"], rel=0.15)
