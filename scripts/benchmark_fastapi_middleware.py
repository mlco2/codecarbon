"""Benchmark FastAPI middleware overhead with a realistic ML inference workload.

Run from repo root (embedder workload, mocked tracker delay):

    uv run --extra fastapi --with uvicorn --with sentence-transformers \\
        python scripts/benchmark_fastapi_middleware.py

Use ``--real-tracker`` to measure with a live :class:`~codecarbon.EmissionsTracker`
(``save_to_file=False``). Use ``--workload noop`` for handler-only baseline.
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable
from unittest.mock import MagicMock, patch

from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI

import codecarbon.integrations.fastapi.middleware as cc_fastapi_middleware
from codecarbon.integrations.fastapi import add_codecarbon_middleware

DEFAULT_MEASUREMENT_DELAY_S = 0.02
WARMUP_REQUESTS = 50
BENCHMARK_REQUESTS = 300
CONCURRENCY = 8
TRACKER_KWARGS = {"save_to_file": False, "save_to_api": False}
DEFAULT_EMBEDDER_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"
DEFAULT_CLASSIFIER_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
SAMPLE_TEXT = "CodeCarbon measures the carbon footprint of machine learning workloads."


@dataclass(frozen=True)
class BenchmarkResult:
    """Aggregated HTTP benchmark metrics for one configuration."""

    name: str
    requests: int
    concurrency: int
    mean_ms: float
    median_ms: float
    p95_ms: float
    requests_per_sec: float
    overhead_pct: float | None


def _mock_emissions_data(measurement_delay_s: float) -> MagicMock:
    return MagicMock(
        emissions=0.001,
        duration=measurement_delay_s,
        energy_consumed=0.002,
        emissions_rate=0.002,
    )


def _install_tracker_patch(measurement_delay_s: float) -> Any:
    def _stop() -> float:
        time.sleep(measurement_delay_s)
        return 0.001

    tracker = MagicMock()
    tracker.start.return_value = None
    tracker.stop.side_effect = _stop
    tracker.start_task.return_value = None
    tracker.stop_task.side_effect = lambda _name: _mock_emissions_data(
        measurement_delay_s
    )
    tracker.final_emissions_data = _mock_emissions_data(measurement_delay_s)
    return patch.object(cc_fastapi_middleware, "EmissionsTracker", return_value=tracker)


def _logging_callback(logger: logging.Logger) -> Callable[..., None]:
    def _on_complete(
        request: Any, response: Any, emissions_data: Any, task_name: str
    ) -> None:
        emissions = getattr(emissions_data, "emissions", None)
        logger.info(
            "%s emissions=%s status=%s",
            task_name,
            emissions,
            response.status_code,
        )

    return _on_complete


def _benchmark_logger() -> logging.Logger:
    """Logger that records messages without terminal I/O noise."""
    benchmark_logger = logging.getLogger("codecarbon.benchmark")
    benchmark_logger.setLevel(logging.INFO)
    benchmark_logger.propagate = False
    if not benchmark_logger.handlers:
        handler = logging.FileHandler(os.devnull)
        handler.setLevel(logging.INFO)
        benchmark_logger.addHandler(handler)
    return benchmark_logger


class InferenceWorkload:
    """Runs a small Hugging Face model once per request."""

    def __init__(self, workload: str, model_id: str) -> None:
        self.workload = workload
        self.model_id = model_id
        self._embedder: Any = None
        self._classifier: Any = None

    def load(self) -> None:
        """Load the model into memory (call once per server process)."""
        if self.workload == "noop":
            return
        if self.workload == "hf-embedder":
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(self.model_id)
            return
        if self.workload == "hf-classifier":
            from transformers import pipeline

            self._classifier = pipeline(
                "sentiment-analysis",
                model=self.model_id,
                device=-1,
            )
            return
        raise ValueError(f"Unknown workload: {self.workload}")

    def run(self, text: str = SAMPLE_TEXT) -> dict[str, Any]:
        """Execute one inference and return a small JSON-serializable payload."""
        if self.workload == "noop":
            return {"ok": True}
        if self.workload == "hf-embedder":
            vector = self._embedder.encode(text)
            return {"dimensions": int(vector.shape[0])}
        if self.workload == "hf-classifier":
            result = self._classifier(text[:512])[0]
            return {"label": result["label"], "score": float(result["score"])}
        raise ValueError(f"Unknown workload: {self.workload}")


def build_app(mode: str, workload: InferenceWorkload) -> FastAPI:
    """Build a FastAPI app for the given benchmark mode."""
    benchmark_logger = _benchmark_logger()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        workload.load()
        yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict(text: str = SAMPLE_TEXT) -> dict[str, Any]:
        return workload.run(text)

    if mode == "baseline":
        return application

    kwargs: dict[str, Any] = {
        "tracking_mode": "request",
        "response_headers": "default",
        "tracker_kwargs": TRACKER_KWARGS,
        "exclude": [],
    }
    if mode == "sync_no_logging":
        pass
    elif mode == "sync_logging":
        kwargs["on_request_complete"] = _logging_callback(benchmark_logger)
    elif mode == "deferred_logging":
        kwargs["defer_measurement"] = True
        kwargs["response_headers"] = None
        kwargs["on_request_complete"] = _logging_callback(benchmark_logger)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    add_codecarbon_middleware(application, **kwargs)
    return application


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * pct) - 1))
    return ordered[index]


def _run_load(base_url: str, requests: int, concurrency: int) -> list[float]:
    latencies_ms: list[float] = []

    def _get(client: httpx.Client) -> float:
        start = time.perf_counter()
        response = client.get(f"{base_url}/predict", timeout=120.0)
        response.raise_for_status()
        return (time.perf_counter() - start) * 1000

    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(_get, client) for _ in range(requests)]
            for future in futures:
                latencies_ms.append(future.result())
    return latencies_ms


def _summarize(
    name: str,
    latencies_ms: list[float],
    concurrency: int,
    baseline_mean_ms: float | None,
) -> BenchmarkResult:
    total_s = sum(latencies_ms) / 1000
    mean_ms = statistics.mean(latencies_ms)
    overhead = None
    if baseline_mean_ms and baseline_mean_ms > 0:
        overhead = ((mean_ms - baseline_mean_ms) / baseline_mean_ms) * 100
    return BenchmarkResult(
        name=name,
        requests=len(latencies_ms),
        concurrency=concurrency,
        mean_ms=mean_ms,
        median_ms=statistics.median(latencies_ms),
        p95_ms=_percentile(latencies_ms, 0.95),
        requests_per_sec=len(latencies_ms) / total_s if total_s else 0.0,
        overhead_pct=overhead,
    )


def _wait_for_server(base_url: str, timeout_s: float = 120.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            httpx.get(f"{base_url}/predict", timeout=30.0)
            return
        except (httpx.HTTPError, OSError):
            time.sleep(0.1)
    raise RuntimeError(f"Server at {base_url} did not become ready")


def _run_scenario(
    mode: str,
    display_name: str,
    port: int,
    requests: int,
    warmup: int,
    concurrency: int,
    measurement_delay_s: float,
    workload: InferenceWorkload,
    real_tracker: bool,
) -> BenchmarkResult:
    app = build_app(mode, workload)
    patcher = None
    if mode != "baseline" and not real_tracker:
        patcher = _install_tracker_patch(measurement_delay_s)
    if patcher is not None:
        patcher.start()

    config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="error", access_log=False
    )
    server = uvicorn.Server(config)

    def _serve() -> None:
        server.run()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_server(base_url)
        _run_load(base_url, warmup, concurrency)
        drain_s = measurement_delay_s * 4 if mode == "deferred_logging" else 0.0
        if drain_s and not real_tracker:
            time.sleep(drain_s)
        latencies = _run_load(base_url, requests, concurrency)
        if drain_s:
            time.sleep(drain_s)
        return _summarize(display_name, latencies, concurrency, None)
    finally:
        server.should_exit = True
        thread.join(timeout=10.0)
        if patcher is not None:
            patcher.stop()


def _format_results(
    results: list[BenchmarkResult],
    *,
    workload: str,
    model_id: str,
    real_tracker: bool,
    measurement_delay_ms: float | None,
) -> str:
    baseline_mean = results[0].mean_ms
    lines = [
        f"Platform: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {sys.version.split()[0]}",
        f"Workload: {workload} ({model_id})",
        f"EmissionsTracker: {'live' if real_tracker else f'mocked ({measurement_delay_ms:.0f} ms stop delay)'}",
        f"Requests per scenario: {results[0].requests} (warmup excluded), "
        f"concurrency: {results[0].concurrency}",
        "",
        "| Configuration | Mean (ms) | Median (ms) | p95 (ms) | req/s | vs baseline |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for index, result in enumerate(results):
        overhead = result.overhead_pct
        if overhead is None and index > 0:
            overhead = (
                (result.mean_ms - baseline_mean) / baseline_mean * 100
                if baseline_mean
                else None
            )
        overhead_str = "—" if index == 0 else f"+{overhead:.1f}%"
        lines.append(
            f"| {result.name} | {result.mean_ms:.2f} | {result.median_ms:.2f} | "
            f"{result.p95_ms:.2f} | {result.requests_per_sec:.1f} | {overhead_str} |"
        )
    return "\n".join(lines)


def run_benchmarks(
    *,
    requests: int = BENCHMARK_REQUESTS,
    warmup: int = WARMUP_REQUESTS,
    concurrency: int = CONCURRENCY,
    measurement_delay_s: float = DEFAULT_MEASUREMENT_DELAY_S,
    workload_name: str,
    model_id: str,
    real_tracker: bool,
) -> list[BenchmarkResult]:
    """Run all benchmark scenarios and return summarized results."""
    workload = InferenceWorkload(workload_name, model_id)
    scenarios = [
        ("baseline", "No middleware"),
        ("sync_no_logging", "Middleware, sync (headers, no logging)"),
        ("sync_logging", "Middleware, sync + logging callback"),
        ("deferred_logging", "Middleware, deferred + logging callback"),
    ]
    results: list[BenchmarkResult] = []
    for index, (mode, label) in enumerate(scenarios):
        port = 8765 + index
        results.append(
            _run_scenario(
                mode,
                label,
                port,
                requests,
                warmup,
                concurrency,
                measurement_delay_s,
                workload,
                real_tracker,
            )
        )
    baseline_mean = results[0].mean_ms
    return [
        BenchmarkResult(
            name=r.name,
            requests=r.requests,
            concurrency=r.concurrency,
            mean_ms=r.mean_ms,
            median_ms=r.median_ms,
            p95_ms=r.p95_ms,
            requests_per_sec=r.requests_per_sec,
            overhead_pct=None
            if i == 0
            else ((r.mean_ms - baseline_mean) / baseline_mean * 100),
        )
        for i, r in enumerate(results)
    ]


def _resolve_model_id(workload: str, model_id: str | None) -> str:
    if model_id:
        return model_id
    if workload == "hf-embedder":
        return DEFAULT_EMBEDDER_MODEL
    if workload == "hf-classifier":
        return DEFAULT_CLASSIFIER_MODEL
    return "n/a"


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=int, default=BENCHMARK_REQUESTS)
    parser.add_argument("--warmup", type=int, default=WARMUP_REQUESTS)
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY)
    parser.add_argument(
        "--workload",
        choices=("noop", "hf-embedder", "hf-classifier"),
        default="hf-embedder",
    )
    parser.add_argument("--model", default=None, help="Hugging Face model id override")
    parser.add_argument(
        "--real-tracker",
        action="store_true",
        help="Use a live EmissionsTracker instead of a mocked stop() delay",
    )
    parser.add_argument(
        "--measurement-delay-ms",
        type=float,
        default=DEFAULT_MEASUREMENT_DELAY_S * 1000,
        help="Mocked tracker stop() duration when --real-tracker is not set",
    )
    args = parser.parse_args()
    model_id = _resolve_model_id(args.workload, args.model)
    measurement_delay_s = args.measurement_delay_ms / 1000

    results = run_benchmarks(
        requests=args.requests,
        warmup=args.warmup,
        concurrency=args.concurrency,
        measurement_delay_s=measurement_delay_s,
        workload_name=args.workload,
        model_id=model_id,
        real_tracker=args.real_tracker,
    )
    delay_label = None if args.real_tracker else args.measurement_delay_ms
    print(
        _format_results(
            results,
            workload=args.workload,
            model_id=model_id,
            real_tracker=args.real_tracker,
            measurement_delay_ms=delay_label or 0.0,
        )
    )


if __name__ == "__main__":
    main()
