#!/usr/bin/env python3
"""Verify FastAPI middleware logging, CSV, and optional API upload.

Per-request emissions appear in logs via ``on_request_complete`` (default).
CSV rows and API ``add_emission`` calls are written when the shared tracker
stops (use ``create_codecarbon_lifespan``), not after each ``stop_task``.

Examples:
    uv run --extra fastapi python scripts/verify_fastapi_middleware_outputs.py
    uv run --extra fastapi python scripts/verify_fastapi_middleware_outputs.py --save-to-api
"""

from __future__ import annotations

import argparse
import logging
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient

import codecarbon.integrations.fastapi.middleware as cc_fastapi_middleware
from codecarbon.core.api_client import ApiClient
from codecarbon.core.config import get_hierarchical_config
from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    create_codecarbon_lifespan,
)
from codecarbon.integrations.fastapi.middleware import log_request_complete


class _LogCounter(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.request_log_lines = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.name != "codecarbon":
            return
        message = record.getMessage()
        if message.startswith("CodeCarbon ") and "emissions=" in message:
            self.request_log_lines += 1


def _build_app(
    *,
    output_dir: Path,
    save_to_api: bool,
    project_name: str,
) -> FastAPI:
    tracker_kwargs: dict[str, Any] = {
        "save_to_file": True,
        "save_to_api": save_to_api,
        "save_to_logger": False,
        "output_dir": str(output_dir),
        "measure_power_secs": 2,
        "api_call_interval": 1,
        "allow_multiple_runs": True,
    }

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with create_codecarbon_lifespan(
            application,
            project_name=project_name,
            **tracker_kwargs,
        ):
            yield

    application = FastAPI(lifespan=lifespan)
    add_codecarbon_middleware(
        application,
        project_name=project_name,
        tracker_kwargs=tracker_kwargs,
        on_request_complete=log_request_complete,
    )

    @application.get("/predict")
    def predict(text: str = "hello") -> dict[str, str]:
        return {"text": text, "label": "demo"}

    return application


def _count_run_emissions(api: ApiClient, run_id: str) -> int:
    url = f"{api.url}/runs/{run_id}/emissions"
    response = requests.get(url, headers=api._get_headers(), timeout=15)
    if response.status_code != 200:
        return 0
    payload = response.json()
    items = payload.get("items") or payload.get("data") or []
    if isinstance(items, list):
        return len(items)
    return 0


def _get_api_client_from_config() -> ApiClient | None:
    conf = get_hierarchical_config()
    section = conf.get("codecarbon", conf)
    api_key = section.get("api_key") or section.get("api_token")
    experiment_id = section.get("experiment_id")
    endpoint = section.get("api_endpoint") or "https://api.codecarbon.io"
    if not api_key or not experiment_id:
        return None
    return ApiClient(
        endpoint_url=endpoint,
        experiment_id=experiment_id,
        api_key=api_key,
        conf=conf,
        create_run_automatically=False,
    )


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--save-to-api",
        action="store_true",
        help="Enable save_to_api using ~/.codecarbon.config (requires api_key).",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=3,
        help="Number of GET /predict calls (default: 3).",
    )
    args = parser.parse_args(argv)

    save_to_api = args.save_to_api
    if save_to_api:
        api_probe = _get_api_client_from_config()
        if api_probe is None:
            print(
                "ERROR: --save-to-api needs api_key and experiment_id in "
                "~/.codecarbon.config",
                file=sys.stderr,
            )
            return 1
        if api_probe.check_auth() is None:
            print(
                "WARN: /auth/check failed; continuing (upload probe uses run emissions)."
            )

    log_counter = _LogCounter()
    cc_fastapi_middleware.logger.addHandler(log_counter)

    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="cc-fastapi-verify-") as tmp:
            output_dir = Path(tmp)
            app = _build_app(
                output_dir=output_dir,
                save_to_api=save_to_api,
                project_name="fastapi-verify",
            )
            run_id: str | None = None
            with TestClient(app) as client:
                for _ in range(args.requests):
                    response = client.get("/predict", params={"text": "verify"})
                    if response.status_code != 200:
                        failures.append(
                            f"predict returned status {response.status_code}"
                        )
                        break
                tracker = getattr(app.state, "codecarbon_tracker", None)
                if tracker is not None:
                    for handler in tracker._output_handlers:
                        handler_run_id = getattr(handler, "run_id", None)
                        if handler_run_id:
                            run_id = handler_run_id
                            break

            if log_counter.request_log_lines < args.requests:
                failures.append(
                    f"expected {args.requests} per-request log lines, got "
                    f"{log_counter.request_log_lines}"
                )
            else:
                print(
                    f"OK: {log_counter.request_log_lines} per-request log line(s) "
                    "(on_request_complete)"
                )

            emissions_csv = output_dir / "emissions.csv"
            if not emissions_csv.is_file() or emissions_csv.stat().st_size == 0:
                failures.append(
                    f"missing or empty CSV at {emissions_csv} (written on tracker.stop)"
                )
            else:
                line_count = len(emissions_csv.read_text().splitlines())
                print(
                    f"OK: CSV {emissions_csv} ({line_count} line(s) including header)"
                )

            task_csvs = list(output_dir.glob("emissions_*.csv"))
            if task_csvs:
                print(f"OK: task CSV(s): {', '.join(p.name for p in task_csvs)}")
            else:
                print(
                    "NOTE: no per-task CSV (emissions_<experiment>_<run_id>.csv); "
                    "run-level emissions.csv is the main artifact on stop"
                )

            if save_to_api:
                api = _get_api_client_from_config()
                if api is None or run_id is None:
                    failures.append("could not resolve API client or run_id after stop")
                else:
                    count = _count_run_emissions(api, run_id)
                    if count < 1:
                        failures.append(
                            f"no emissions listed for run {run_id} at "
                            f"{api.url}/runs/.../emissions"
                        )
                    else:
                        print(f"OK: API run {run_id} has {count} emission record(s)")
    finally:
        cc_fastapi_middleware.logger.removeHandler(log_counter)

    if failures:
        for msg in failures:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
