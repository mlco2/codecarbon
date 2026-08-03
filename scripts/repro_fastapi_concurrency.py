#!/usr/bin/env python3
"""Repro: live tracker + concurrent FastAPI requests.

Uses the embedder from examples/fastapi_concurrency.py. Pass --lazy to exercise
middleware-only tracker startup (no lifespan).

    uv run --extra fastapi --with uvicorn --with httpx --with sentence-transformers --with torch \\
        python scripts/repro_fastapi_concurrency.py

    uv run ... python scripts/repro_fastapi_concurrency.py --lazy
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import httpx
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.fastapi_concurrency import SAMPLE_TEXT, app_lazy, app_lifespan

logging.basicConfig(level=logging.ERROR)
codecarbon_logger = logging.getLogger("codecarbon")
errors: list[str] = []


class _ErrorCapture(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR and "_active_task_emissions_at_start" in record.getMessage():
            errors.append(record.getMessage())


codecarbon_logger.addHandler(_ErrorCapture())


async def fire_requests(base_url: str, n: int, concurrency: int) -> None:
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(base_url=base_url, timeout=120.0) as client:
        await client.get("/embed", params={"text": SAMPLE_TEXT})

        async def one() -> None:
            async with sem:
                response = await client.get("/embed", params={"text": SAMPLE_TEXT})
                response.raise_for_status()

        await asyncio.gather(*(one() for _ in range(n)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lazy",
        action="store_true",
        help="Use app_lazy (middleware creates tracker) instead of lifespan app",
    )
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    app = app_lazy if args.lazy else app_lifespan
    mode = "lazy" if args.lazy else "lifespan"
    host, port = "127.0.0.1", 0
    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)

    async def run() -> None:
        serve_task = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.05)
        bound_port = server.servers[0].sockets[0].getsockname()[1]
        base_url = f"http://{host}:{bound_port}"
        await fire_requests(
            base_url,
            n=args.requests,
            concurrency=args.concurrency,
        )
        server.should_exit = True
        await serve_task

    asyncio.run(run())

    if errors:
        print(
            f"FAIL [{mode}]: {len(errors)} _active_task_emissions_at_start error(s)",
            file=sys.stderr,
        )
        for msg in errors[:5]:
            print(f"  {msg}", file=sys.stderr)
        return 1
    print(f"OK [{mode}]: no concurrency errors ({args.requests} req, c={args.concurrency})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
