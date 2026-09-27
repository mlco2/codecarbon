"""Per-request overhead of ``CodeCarbonMiddleware``.

Times 100k in-process ASGI calls of a trivial app, with and without the
middleware, and prints p50/p99 per call. Budget: at most 30 µs (Linux) or
50 µs (macOS) added at p50. Run with::

    uv run python tests/integrations/fastapi_overhead.py

A sampling window is closed every 1000 requests, outside the timed calls, so
the in-flight table stays at a realistic size.
"""

import asyncio
import statistics
import sys
import time

from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.integrations.fastapi import CodeCarbonMiddleware

N = 100_000
WINDOW_EVERY = 1000
SCOPE = {"type": "http", "method": "GET", "path": "/", "headers": []}


async def _app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


async def _receive():
    return {"type": "http.request", "body": b"", "more_body": False}


async def _send(message):
    pass


async def _time(app, on_window=None) -> list[int]:
    durations = []
    for i in range(N):
        start = time.perf_counter_ns()
        await app(dict(SCOPE), _receive, _send)
        durations.append(time.perf_counter_ns() - start)
        if on_window is not None and i % WINDOW_EVERY == WINDOW_EVERY - 1:
            on_window()
    return durations


def _summary(name: str, durations: list[int]) -> float:
    q = statistics.quantiles(durations, n=100)
    p50, p99 = q[49] / 1000, q[98] / 1000
    print(f"{name:>16}: p50 {p50:7.2f} µs  p99 {p99:7.2f} µs")
    return p50


def main() -> None:
    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        measure_power_secs=3600,  # windows are closed by hand
        output_methods=[],
        allow_multiple_runs=True,
        log_level="error",
    )
    tracker.start()
    try:
        middleware = CodeCarbonMiddleware(_app, tracker=tracker, on_request=None)
        asyncio.run(_time(_app))  # warm-up
        bare = _summary("bare", asyncio.run(_time(_app)))
        metered = _summary(
            "with middleware",
            asyncio.run(_time(middleware, tracker._measure_power_and_energy)),
        )
    finally:
        tracker.stop()
    budget = 30.0 if sys.platform.startswith("linux") else 50.0
    added = metered - bare
    print(f"{'added':>16}: p50 {added:7.2f} µs (budget {budget:.0f} µs)")
    sys.exit(0 if added <= budget else 1)


if __name__ == "__main__":
    main()
