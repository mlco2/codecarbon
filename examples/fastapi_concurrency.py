"""Concurrent FastAPI + live tracker: what breaks and what works.

Root cause of ``_active_task_emissions_at_start was None`` under load
--------------------------------------------------------------------
``EmissionsTracker.start_task`` / ``stop_task`` assume **one** active task
(``_active_task``, ``_active_task_emissions_at_start``). Concurrent HTTP
requests that call ``start_task`` while another request is in flight either
bail out ("A task is already under measure") or corrupt shared state; the
next ``stop_task`` then logs the error and reports zero delta.

The middleware avoids this whenever the tracker is already running
(``tracker.start()`` was called) by using per-request baselines::

    mark_http_request_start("GET /embed")  -> HttpRequestBaseline
    ... handle request ...
    finish_http_request(baseline)

That path is concurrency-safe (unique internal task names, locks).

**Recommended:** ``create_codecarbon_lifespan`` (see ``fastapi_embedder.py``).
**Also OK:** middleware-only lazy ``tracker.start()`` — same mark/finish path
after the fix in ``CodeCarbonMiddleware._begin_request``.

Run the embedder with lifespan (production-style)::

    uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \\
        uvicorn examples.fastapi_concurrency:app_lifespan --host 127.0.0.1 --port 8000

Run the minimal lazy-tracker variant (no lifespan)::

    uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \\
        uvicorn examples.fastapi_concurrency:app_lazy --host 127.0.0.1 --port 8001

Load test (20 requests, concurrency 4)::

    uv run --extra fastapi --with httpx python examples/fastapi_concurrency.py \\
        --url http://127.0.0.1:8000/embed
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

import httpx
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    create_codecarbon_lifespan,
)

MODEL_ID = "sentence-transformers/paraphrase-MiniLM-L3-v2"
SAMPLE_TEXT = "CodeCarbon measures the carbon footprint of machine learning workloads."

_TRACKER_KWARGS = {
    "save_to_file": False,
    "save_to_api": False,
    "save_to_logger": False,
    "allow_multiple_runs": True,
    "measure_power_secs": 2,
}


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_ID)


def _build_routes(application: FastAPI) -> None:
    @application.get("/embed")
    def embed(text: str = SAMPLE_TEXT) -> dict[str, Any]:
        vector = _load_model().encode(text)
        return {"dimensions": int(vector.shape[0]), "model": MODEL_ID}


def _wire_middleware(application: FastAPI) -> None:
    add_codecarbon_middleware(
        application,
        project_name="fastapi-concurrency",
        tracker_kwargs=_TRACKER_KWARGS,
        on_request_complete=None,
    )


@asynccontextmanager
async def _lifespan(application: FastAPI):
    _load_model()
    async with create_codecarbon_lifespan(
        application,
        project_name="fastapi-concurrency",
        **_TRACKER_KWARGS,
    ):
        yield


app_lifespan = FastAPI(title="CodeCarbon concurrency (lifespan)", lifespan=_lifespan)
_build_routes(app_lifespan)
_wire_middleware(app_lifespan)

app_lazy = FastAPI(title="CodeCarbon concurrency (lazy tracker)")
_build_routes(app_lazy)
_wire_middleware(app_lazy)


@app_lazy.on_event("startup")
def _warmup_lazy_model() -> None:
    _load_model()


async def _load_test(base_url: str, *, requests: int, concurrency: int) -> None:
    sem = asyncio.Semaphore(concurrency)

    async def one(client: httpx.AsyncClient) -> None:
        async with sem:
            response = await client.get("/embed", params={"text": SAMPLE_TEXT})
            response.raise_for_status()

    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        await asyncio.gather(*(one(client) for _ in range(requests)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of a running app (default: lifespan app on :8000)",
    )
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args(argv)

    captured: list[str] = []

    class _ErrorCapture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if (
                record.levelno >= logging.ERROR
                and "_active_task_emissions_at_start" in record.getMessage()
            ):
                captured.append(record.getMessage())

    codecarbon_logger = logging.getLogger("codecarbon")
    codecarbon_logger.addHandler(_ErrorCapture())
    try:
        asyncio.run(
            _load_test(
                args.url.rstrip("/"),
                requests=args.requests,
                concurrency=args.concurrency,
            )
        )
    finally:
        codecarbon_logger.removeHandler(_ErrorCapture())

    if captured:
        print(f"FAIL: {len(captured)} concurrency error(s)", file=sys.stderr)
        for message in captured[:5]:
            print(f"  {message}", file=sys.stderr)
        return 1

    print(
        f"OK: {args.requests} requests at concurrency {args.concurrency} "
        f"— no _active_task_emissions_at_start errors"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
