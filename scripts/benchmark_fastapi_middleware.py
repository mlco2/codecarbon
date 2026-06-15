"""Benchmark FastAPI middleware overhead with a realistic ML inference workload.

Run from repo root:

    uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \\
        python scripts/benchmark_fastapi_middleware.py

Uses async HTTP clients (``httpx.AsyncClient``). Reports 95% bootstrap CIs on mean
latency. Verifies default middleware emits one ``codecarbon`` log line per request.

Optional ``--with-save-to-api`` adds a scenario with ``save_to_api=True`` and
``api_call_interval=1`` (API ``live_out`` after each task measurement). Mocked runs
add ``--api-delay-ms`` sleep on ``stop_task``; ``--real-tracker`` patches
``ApiClient`` instead of calling the network.

Use ``--quick`` for in-process ASGI (no uvicorn per scenario), noop workload, and
normal-approx CIs. ML workloads are preloaded once across scenarios when using HF.
"""

from __future__ import annotations

import os

os.environ.setdefault("CODECARBON_LOG_LEVEL", "ERROR")

import argparse
import asyncio
import logging
import platform
import random
import statistics
import sys
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
from fastapi import FastAPI

import codecarbon.integrations.fastapi.middleware as cc_fastapi_middleware
from codecarbon.external.logger import logger as codecarbon_logger
from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    shutdown_codecarbon_middleware,
)

DEFAULT_MEASUREMENT_DELAY_S = 0.02
WARMUP_REQUESTS = 50
BENCHMARK_REQUESTS = 300
QUICK_WARMUP_REQUESTS = 5
QUICK_BENCHMARK_REQUESTS = 50
QUICK_SECONDARY_WARMUP = 2
SMOKE_WARMUP_REQUESTS = 2
SMOKE_BENCHMARK_REQUESTS = 20
SMOKE_INFERENCE_DELAY_MS = 15.0
QUICK_LOGGING_SAMPLE = 10
CONCURRENCY = 8
BOOTSTRAP_SAMPLES = 2000
QUICK_BOOTSTRAP_SAMPLES = 200
FINALIZE_DRAIN_MULTIPLIER = 4
QUICK_INFERENCE_DELAY_MS = 25.0
CONFIDENCE_LEVEL = 0.95
FASTAPI_BENCHMARK_PROJECT_ID = "25bf2346-49de-4658-911e-4c9003000e13"
FASTAPI_BENCHMARK_EXPERIMENT_ID = "d2d69403-1373-42b4-a2c1-09589aed4801"
REALISTIC_BENCHMARK_REQUESTS = 50
REALISTIC_WARMUP_REQUESTS = 5
REALISTIC_CONCURRENCY = 4
TRACKER_KWARGS = {"save_to_file": False, "save_to_api": False}
TRACKER_KWARGS_SAVE_TO_API = {
    "save_to_file": False,
    "save_to_api": True,
    "save_to_logger": False,
    "api_call_interval": 1,
    "experiment_id": FASTAPI_BENCHMARK_EXPERIMENT_ID,
}
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
    ci_low_ms: float
    ci_high_ms: float
    median_ms: float
    p95_ms: float
    requests_per_sec: float
    overhead_pct: float | None
    codecarbon_log_lines: int | None = None


def _mock_emissions_data(measurement_delay_s: float) -> MagicMock:
    return MagicMock(
        emissions=0.001,
        duration=measurement_delay_s,
        energy_consumed=0.002,
        emissions_rate=0.002,
    )


def _install_tracker_patch(
    measurement_delay_s: float,
    *,
    api_delay_state: dict[str, float] | None = None,
    api_delay_s: float = 0.0,
) -> Any:
    delays = api_delay_state if api_delay_state is not None else {"api": api_delay_s}

    def _stop() -> float:
        time.sleep(measurement_delay_s)
        return 0.001

    def _stop_task(_name: str) -> MagicMock:
        time.sleep(measurement_delay_s)
        if delays.get("api", 0.0) > 0:
            time.sleep(delays["api"])
        return _mock_emissions_data(measurement_delay_s)

    tracker = MagicMock()
    tracker.start.return_value = None
    tracker.stop.side_effect = _stop
    tracker.start_task.return_value = None
    tracker.stop_task.side_effect = _stop_task
    tracker.persist_completed_task.return_value = None
    tracker.final_emissions_data = _mock_emissions_data(measurement_delay_s)
    return patch.object(cc_fastapi_middleware, "EmissionsTracker", return_value=tracker)


def _config_ids() -> tuple[str, str]:
    """Read project_id and experiment_id from hierarchical config when present."""
    from codecarbon.core.config import get_hierarchical_config

    section = get_hierarchical_config()
    project_id = section.get("project_id") or FASTAPI_BENCHMARK_PROJECT_ID
    experiment_id = section.get("experiment_id") or FASTAPI_BENCHMARK_EXPERIMENT_ID
    return project_id, experiment_id


def _install_api_client_patch(api_delay_s: float) -> Any:
    """Avoid network I/O while exercising ``save_to_api`` output handlers."""

    import uuid

    from codecarbon.core import api_client as api_client_module

    def _create_run(self: Any, experiment_id: str) -> None:
        self.run_id = str(uuid.uuid4())

    def _add_emission(self: Any, carbon_emission: dict) -> bool:
        time.sleep(api_delay_s)
        return True

    return patch.multiple(
        api_client_module.ApiClient,
        _create_run=_create_run,
        add_emission=_add_emission,
    )


_Z_95 = 1.96


def bootstrap_mean_ci(
    latencies_ms: list[float],
    *,
    samples: int = BOOTSTRAP_SAMPLES,
    confidence: float = CONFIDENCE_LEVEL,
) -> tuple[float, float, float]:
    """Return mean and two-sided bootstrap CI bounds for mean latency."""
    if not latencies_ms:
        return 0.0, 0.0, 0.0
    n = len(latencies_ms)
    boot_means = [
        statistics.mean(random.choices(latencies_ms, k=n)) for _ in range(samples)
    ]
    boot_means.sort()
    alpha = (1.0 - confidence) / 2.0
    low_index = max(0, int(alpha * samples) - 1)
    high_index = min(samples - 1, int((1.0 - alpha) * samples))
    return (
        statistics.mean(latencies_ms),
        boot_means[low_index],
        boot_means[high_index],
    )


def normal_mean_ci(latencies_ms: list[float]) -> tuple[float, float, float]:
    """Approximate 95% CI for the mean (faster than bootstrap for --quick)."""
    if not latencies_ms:
        return 0.0, 0.0, 0.0
    n = len(latencies_ms)
    mean = statistics.mean(latencies_ms)
    if n < 2:
        return mean, mean, mean
    margin = _Z_95 * statistics.stdev(latencies_ms) / (n**0.5)
    return mean, mean - margin, mean + margin


def summarize_latencies(
    latencies_ms: list[float],
    *,
    bootstrap_samples: int,
    use_normal_ci: bool,
) -> tuple[float, float, float, float, float]:
    """Return mean, CI low/high, median, and p95."""
    if use_normal_ci:
        mean_ms, ci_low_ms, ci_high_ms = normal_mean_ci(latencies_ms)
    else:
        mean_ms, ci_low_ms, ci_high_ms = bootstrap_mean_ci(
            latencies_ms, samples=bootstrap_samples
        )
    return (
        mean_ms,
        ci_low_ms,
        ci_high_ms,
        statistics.median(latencies_ms),
        _percentile(latencies_ms, 0.95),
    )


class InferenceWorkload:
    """Runs a small Hugging Face model once per request."""

    def __init__(
        self,
        workload: str,
        model_id: str,
        *,
        inference_delay_s: float = 0.0,
    ) -> None:
        self.workload = workload
        self.model_id = model_id
        self.inference_delay_s = inference_delay_s
        self._embedder: Any = None
        self._classifier: Any = None
        self._loaded = False

    def ensure_loaded(self) -> None:
        """Load the model at most once (shared across benchmark scenarios)."""
        if self._loaded:
            return
        self.load()
        self._loaded = True

    def load(self) -> None:
        """Load the model into memory."""
        if self.workload == "noop":
            self._loaded = True
            return
        if self.workload == "hf-embedder":
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(self.model_id)
            self._loaded = True
            return
        if self.workload == "hf-classifier":
            from transformers import pipeline

            self._classifier = pipeline(
                "sentiment-analysis",
                model=self.model_id,
                device=-1,
            )
            self._loaded = True
            return
        raise ValueError(f"Unknown workload: {self.workload}")

    def run(self, text: str = SAMPLE_TEXT) -> dict[str, Any]:
        """Execute one inference and return a small JSON-serializable payload."""
        if self.inference_delay_s > 0:
            time.sleep(self.inference_delay_s)
        if self.workload == "noop":
            return {"ok": True}
        if self.workload == "hf-embedder":
            vector = self._embedder.encode(text)
            return {"dimensions": int(vector.shape[0])}
        if self.workload == "hf-classifier":
            result = self._classifier(text[:512])[0]
            return {"label": result["label"], "score": float(result["score"])}
        raise ValueError(f"Unknown workload: {self.workload}")


def build_app(
    mode: str,
    workload: InferenceWorkload,
    *,
    project_name: str = FASTAPI_BENCHMARK_PROJECT_ID,
    experiment_id: str = FASTAPI_BENCHMARK_EXPERIMENT_ID,
    real_tracker: bool = False,
) -> FastAPI:
    """Build a FastAPI app for the given benchmark mode."""
    if real_tracker and mode != "baseline":
        from codecarbon.integrations.fastapi import create_codecarbon_lifespan

        tracker_kwargs = (
            TRACKER_KWARGS_SAVE_TO_API
            if mode == "deferred_save_to_api"
            else TRACKER_KWARGS
        )
        if mode == "deferred_save_to_api":
            tracker_kwargs = {**tracker_kwargs, "experiment_id": experiment_id}

        @asynccontextmanager
        async def lifespan(_app: FastAPI):
            workload.ensure_loaded()
            async with create_codecarbon_lifespan(
                _app,
                project_name=project_name,
                allow_multiple_runs=True,
                **tracker_kwargs,
            ):
                yield

    else:

        @asynccontextmanager
        async def lifespan(_app: FastAPI):
            workload.ensure_loaded()
            yield

    application = FastAPI(lifespan=lifespan)

    @application.get("/predict")
    def predict(text: str = SAMPLE_TEXT) -> dict[str, Any]:
        return workload.run(text)

    if mode == "baseline":
        return application

    kwargs: dict[str, Any] = {
        "tracker_kwargs": TRACKER_KWARGS,
        "exclude": [],
    }
    if mode == "deferred_no_logging":
        kwargs["on_request_complete"] = None
    elif mode == "deferred_logging":
        pass
    elif mode == "deferred_save_to_api":
        kwargs["tracker_kwargs"] = {
            **TRACKER_KWARGS_SAVE_TO_API,
            "experiment_id": experiment_id,
        }
        kwargs["on_request_complete"] = None
    else:
        raise ValueError(f"Unknown mode: {mode}")

    add_codecarbon_middleware(application, project_name=project_name, **kwargs)
    return application


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * pct) - 1))
    return ordered[index]


class _CodeCarbonLogCounter(logging.Handler):
    """Count ``codecarbon`` INFO lines emitted during a benchmark scenario."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.emissions_lines = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.name != codecarbon_logger.name:
            return
        if record.levelno < logging.INFO:
            return
        message = record.getMessage()
        if message.startswith("CodeCarbon ") and "emissions=" in message:
            self.emissions_lines += 1


async def _run_load_async(
    client: httpx.AsyncClient,
    url: str,
    requests: int,
    concurrency: int,
) -> list[float]:
    """Issue concurrent async GET requests and return client-side latencies (ms)."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _get() -> float:
        async with semaphore:
            start = time.perf_counter()
            response = await client.get(url, timeout=120.0)
            response.raise_for_status()
            return (time.perf_counter() - start) * 1000

    return list(await asyncio.gather(*(_get() for _ in range(requests))))


async def _wait_for_deferred_finalize(
    measurement_delay_s: float,
    *,
    requests: int,
    concurrency: int,
) -> None:
    """Yield until deferred finalize tasks are likely submitted."""
    waves = max(1, (requests + concurrency - 1) // concurrency)
    estimate_s = measurement_delay_s * min(waves, 4)
    await asyncio.sleep(min(0.06, max(0.01, estimate_s)))


def _drain_middleware(app: FastAPI) -> None:
    """Wait for deferred tracker work before tearing down an in-process app."""
    shutdown_codecarbon_middleware(app, wait=True)


def _summarize(
    name: str,
    latencies_ms: list[float],
    concurrency: int,
    baseline_mean_ms: float | None,
    *,
    bootstrap_samples: int,
    use_normal_ci: bool,
    codecarbon_log_lines: int | None = None,
) -> BenchmarkResult:
    total_s = sum(latencies_ms) / 1000
    mean_ms, ci_low_ms, ci_high_ms, median_ms, p95_ms = summarize_latencies(
        latencies_ms,
        bootstrap_samples=bootstrap_samples,
        use_normal_ci=use_normal_ci,
    )
    overhead = None
    if baseline_mean_ms and baseline_mean_ms > 0:
        overhead = ((mean_ms - baseline_mean_ms) / baseline_mean_ms) * 100
    return BenchmarkResult(
        name=name,
        requests=len(latencies_ms),
        concurrency=concurrency,
        mean_ms=mean_ms,
        ci_low_ms=ci_low_ms,
        ci_high_ms=ci_high_ms,
        median_ms=median_ms,
        p95_ms=p95_ms,
        requests_per_sec=len(latencies_ms) / total_s if total_s else 0.0,
        overhead_pct=overhead,
        codecarbon_log_lines=codecarbon_log_lines,
    )


async def _wait_for_server_async(
    client: httpx.AsyncClient, url: str, timeout_s: float = 120.0
) -> None:
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return
        except (httpx.HTTPError, OSError):
            await asyncio.sleep(0.02)
    raise RuntimeError(f"Server at {url} did not become ready")


async def _run_scenario_in_process(
    mode: str,
    display_name: str,
    requests: int,
    warmup: int,
    concurrency: int,
    workload: InferenceWorkload,
    measurement_delay_s: float,
    *,
    real_tracker: bool,
    bootstrap_samples: int,
    use_normal_ci: bool,
    verify_logging: bool,
    logging_sample: int | None,
    experiment_id: str,
    project_name: str,
) -> BenchmarkResult:
    """Benchmark one configuration in-process via ASGI transport."""
    app = build_app(
        mode,
        workload,
        project_name=project_name,
        experiment_id=experiment_id,
        real_tracker=real_tracker,
    )
    workload.ensure_loaded()
    log_counter: _CodeCarbonLogCounter | None = None
    logging_level_restore: int | None = None
    predict_url = "http://benchmark/predict"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, timeout=120.0) as client:
        if warmup > 0:
            await _run_load_async(client, predict_url, warmup, concurrency)
        if verify_logging and mode == "deferred_logging":
            log_counter = _CodeCarbonLogCounter()
            logging_level_restore = codecarbon_logger.level
            codecarbon_logger.setLevel(logging.INFO)
            codecarbon_logger.addHandler(log_counter)
        latencies = await _run_load_async(
            client, predict_url, requests, concurrency
        )
        if mode != "baseline":
            drain_s = 0.5 if real_tracker else measurement_delay_s
            await _wait_for_deferred_finalize(
                drain_s, requests=requests, concurrency=concurrency
            )
        if log_counter is not None:
            expected_logs = logging_sample or requests
            deadline = time.perf_counter() + min(
                2.0,
                measurement_delay_s * (requests / max(concurrency, 1) + 2) + 0.25,
            )
            while (
                log_counter.emissions_lines < expected_logs
                and time.perf_counter() < deadline
            ):
                await asyncio.sleep(0.005)
    log_lines = log_counter.emissions_lines if log_counter is not None else None
    if mode != "baseline":
        _drain_middleware(app)
    if log_counter is not None:
        codecarbon_logger.removeHandler(log_counter)
        if logging_level_restore is not None:
            codecarbon_logger.setLevel(logging_level_restore)
    return _summarize(
        display_name,
        latencies,
        concurrency,
        None,
        bootstrap_samples=bootstrap_samples,
        use_normal_ci=use_normal_ci,
        codecarbon_log_lines=log_lines,
    )


async def _run_scenario_network(
    mode: str,
    display_name: str,
    port: int,
    requests: int,
    warmup: int,
    concurrency: int,
    measurement_delay_s: float,
    workload: InferenceWorkload,
    real_tracker: bool,
    *,
    bootstrap_samples: int,
    use_normal_ci: bool,
    verify_logging: bool,
    api_delay_s: float = 0.0,
    experiment_id: str = FASTAPI_BENCHMARK_EXPERIMENT_ID,
    project_name: str = FASTAPI_BENCHMARK_PROJECT_ID,
) -> BenchmarkResult:
    import uvicorn

    app = build_app(
        mode,
        workload,
        project_name=project_name,
        experiment_id=experiment_id,
        real_tracker=real_tracker,
    )
    api_patcher = None
    uses_save_to_api = mode == "deferred_save_to_api"
    if uses_save_to_api and not real_tracker:
        api_patcher = _install_api_client_patch(api_delay_s)
        api_patcher.start()

    config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="error", access_log=False
    )
    server = uvicorn.Server(config)

    def _serve() -> None:
        server.run()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    predict_url = f"http://127.0.0.1:{port}/predict"
    log_counter: _CodeCarbonLogCounter | None = None
    logging_level_restore: int | None = None
    try:
        async with httpx.AsyncClient() as client:
            await _wait_for_server_async(client, predict_url)
            if warmup > 0:
                await _run_load_async(client, predict_url, warmup, concurrency)
            if mode != "baseline":
                finalize_drain_s = (
                    3.0
                    if real_tracker
                    else measurement_delay_s * FINALIZE_DRAIN_MULTIPLIER
                )
                time.sleep(finalize_drain_s)
            if verify_logging and mode == "deferred_logging":
                log_counter = _CodeCarbonLogCounter()
                logging_level_restore = codecarbon_logger.level
                codecarbon_logger.setLevel(logging.INFO)
                codecarbon_logger.addHandler(log_counter)
            latencies = await _run_load_async(
                client, predict_url, requests, concurrency
            )
            if mode != "baseline":
                time.sleep(
                    3.0
                    if real_tracker
                    else measurement_delay_s * FINALIZE_DRAIN_MULTIPLIER
                )
        log_lines = log_counter.emissions_lines if log_counter is not None else None
        if log_counter is not None:
            codecarbon_logger.removeHandler(log_counter)
            if logging_level_restore is not None:
                codecarbon_logger.setLevel(logging_level_restore)
        return _summarize(
            display_name,
            latencies,
            concurrency,
            None,
            bootstrap_samples=bootstrap_samples,
            use_normal_ci=use_normal_ci,
            codecarbon_log_lines=log_lines,
        )
    finally:
        server.should_exit = True
        thread.join(timeout=3.0)
        if api_patcher is not None:
            api_patcher.stop()


def _format_results(
    results: list[BenchmarkResult],
    *,
    workload: str,
    model_id: str,
    real_tracker: bool,
    measurement_delay_ms: float | None,
    api_delay_ms: float | None,
    with_save_to_api: bool,
    experiment_id: str,
    project_id: str,
    bootstrap_samples: int,
    use_normal_ci: bool,
    in_process: bool,
    logging_verified: bool | None,
) -> str:
    confidence_pct = int(CONFIDENCE_LEVEL * 100)
    ci_method = (
        f"{confidence_pct}% normal approx"
        if use_normal_ci
        else f"{confidence_pct}% bootstrap ({bootstrap_samples} resamples)"
    )
    transport = "in-process ASGI" if in_process else "HTTP (uvicorn)"
    lines = [
        f"Platform: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {sys.version.split()[0]}",
        f"Workload: {workload} ({model_id})",
        f"Transport: {transport}",
        f"HTTP client: async (httpx.AsyncClient)",
        f"EmissionsTracker: {'live' if real_tracker else f'mocked ({measurement_delay_ms:.0f} ms stop delay)'}",
        f"save_to_api scenario: {'yes (api_call_interval=1)' if with_save_to_api else 'no'}",
        f"project_id: {project_id}",
        (
            f"experiment_id (save_to_api): {experiment_id}"
            if with_save_to_api
            else "experiment_id (save_to_api): n/a"
        ),
        (
            f"Mocked API upload delay: {api_delay_ms:.0f} ms"
            if with_save_to_api and api_delay_ms is not None
            else "Mocked API upload delay: n/a"
        ),
        f"Middleware: default deferred measurement",
        f"Logger namespace: {codecarbon_logger.name}",
        f"Requests per scenario: {results[0].requests} (warmup excluded), "
        f"concurrency: {results[0].concurrency}",
        f"Mean CI: {ci_method}",
        "",
        f"| Configuration | Mean (ms) | {confidence_pct}% CI (ms) | Median (ms) | "
        f"p95 (ms) | req/s | vs baseline |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        ci_cell = f"[{result.ci_low_ms:.1f}, {result.ci_high_ms:.1f}]"
        overhead = result.overhead_pct
        if overhead is None:
            overhead_str = "—"
        elif overhead >= 0:
            overhead_str = f"+{overhead:.1f}%"
        else:
            overhead_str = f"{overhead:.1f}%"
        lines.append(
            f"| {result.name} | {result.mean_ms:.2f} | {ci_cell} | "
            f"{result.median_ms:.2f} | {result.p95_ms:.2f} | "
            f"{result.requests_per_sec:.1f} | {overhead_str} |"
        )
    if logging_verified is not None:
        status = "yes" if logging_verified else "no"
        lines.append("")
        lines.append(
            f"CodeCarbon per-request log lines (default middleware): verified={status}"
        )
    return "\n".join(lines)


SCENARIO_KEYS = {
    "no_logging": ("deferred_no_logging", "Deferred, no logging"),
    "logging": ("deferred_logging", "Deferred + logging (default)"),
    "save_to_api": ("deferred_save_to_api", "Deferred + save_to_api (no logging)"),
}


async def _run_benchmarks_async(
    *,
    requests: int,
    warmup: int,
    secondary_warmup: int,
    concurrency: int,
    measurement_delay_s: float,
    workload_name: str,
    model_id: str,
    real_tracker: bool,
    bootstrap_samples: int,
    use_normal_ci: bool,
    verify_logging: bool,
    logging_sample: int | None,
    with_save_to_api: bool,
    scenario_keys: list[str] | None,
    api_delay_s: float,
    experiment_id: str,
    project_id: str,
    inference_delay_s: float,
    in_process: bool,
) -> tuple[list[BenchmarkResult], bool | None]:
    """Run baseline and middleware scenarios."""
    workload = InferenceWorkload(
        workload_name, model_id, inference_delay_s=inference_delay_s
    )
    if workload_name != "noop":
        print(f"Preloading workload {workload_name} ({model_id})...", flush=True)
        workload.ensure_loaded()

    api_delay_state = {"api": 0.0}
    tracker_patcher: Any | None = None
    api_patcher: Any | None = None

    async def _run_one(
        mode: str,
        label: str,
        *,
        port: int | None,
        scenario_warmup: int,
    ) -> BenchmarkResult:
        if in_process:
            return await _run_scenario_in_process(
                mode,
                label,
                requests,
                scenario_warmup,
                concurrency,
                workload,
                measurement_delay_s,
                real_tracker=real_tracker,
                bootstrap_samples=bootstrap_samples,
                use_normal_ci=use_normal_ci,
                verify_logging=verify_logging,
                logging_sample=logging_sample,
                experiment_id=experiment_id,
                project_name=project_id,
            )
        assert port is not None
        return await _run_scenario_network(
            mode,
            label,
            port,
            requests,
            scenario_warmup,
            concurrency,
            measurement_delay_s,
            workload,
            real_tracker,
            bootstrap_samples=bootstrap_samples,
            use_normal_ci=use_normal_ci,
            verify_logging=verify_logging,
            api_delay_s=api_delay_state["api"],
            experiment_id=experiment_id,
            project_name=project_id,
        )

    baseline = await _run_one(
        "baseline",
        "No middleware (baseline)",
        port=8765 if not in_process else None,
        scenario_warmup=warmup,
    )

    scenarios: list[tuple[str, str]] = []
    selected = scenario_keys or ["no_logging", "logging"]
    if with_save_to_api and "save_to_api" not in selected:
        selected = [*selected, "save_to_api"]
    for key in selected:
        if key not in SCENARIO_KEYS:
            raise ValueError(
                f"Unknown scenario {key!r}; choose from {sorted(SCENARIO_KEYS)}"
            )
        scenarios.append(SCENARIO_KEYS[key])

    if not real_tracker:
        tracker_patcher = _install_tracker_patch(
            measurement_delay_s, api_delay_state=api_delay_state
        )
        tracker_patcher.start()

    results: list[BenchmarkResult] = [baseline]
    logging_result: BenchmarkResult | None = None
    try:
        for index, (mode, label) in enumerate(scenarios):
            api_delay_state["api"] = (
                api_delay_s if mode == "deferred_save_to_api" else 0.0
            )
            middleware_warmup = (
                secondary_warmup
                if secondary_warmup > 0
                else min(10, warmup)
                if in_process
                else warmup
            )
            result = await _run_one(
                mode,
                label,
                port=None if in_process else 8766 + index,
                scenario_warmup=middleware_warmup if in_process else warmup,
            )
            if mode == "deferred_logging":
                logging_result = result
            results.append(result)
    finally:
        if api_patcher is not None:
            api_patcher.stop()
        if tracker_patcher is not None:
            tracker_patcher.stop()

    baseline_mean = baseline.mean_ms
    enriched: list[BenchmarkResult] = [
        BenchmarkResult(
            name=baseline.name,
            requests=baseline.requests,
            concurrency=baseline.concurrency,
            mean_ms=baseline.mean_ms,
            ci_low_ms=baseline.ci_low_ms,
            ci_high_ms=baseline.ci_high_ms,
            median_ms=baseline.median_ms,
            p95_ms=baseline.p95_ms,
            requests_per_sec=baseline.requests_per_sec,
            overhead_pct=None,
        )
    ]
    for result in results[1:]:
        enriched.append(
            BenchmarkResult(
                name=result.name,
                requests=result.requests,
                concurrency=result.concurrency,
                mean_ms=result.mean_ms,
                ci_low_ms=result.ci_low_ms,
                ci_high_ms=result.ci_high_ms,
                median_ms=result.median_ms,
                p95_ms=result.p95_ms,
                requests_per_sec=result.requests_per_sec,
                overhead_pct=((result.mean_ms - baseline_mean) / baseline_mean * 100),
                codecarbon_log_lines=result.codecarbon_log_lines,
            )
        )

    logging_verified: bool | None = None
    if logging_result is not None and logging_result.codecarbon_log_lines is not None:
        expected_logs = logging_sample or logging_result.requests
        logging_verified = logging_result.codecarbon_log_lines >= expected_logs
    return enriched, logging_verified


def run_benchmarks(
    *,
    requests: int = BENCHMARK_REQUESTS,
    warmup: int = WARMUP_REQUESTS,
    secondary_warmup: int = 0,
    concurrency: int = CONCURRENCY,
    measurement_delay_s: float = DEFAULT_MEASUREMENT_DELAY_S,
    workload_name: str,
    model_id: str,
    real_tracker: bool,
    bootstrap_samples: int,
    use_normal_ci: bool,
    verify_logging: bool,
    logging_sample: int | None,
    with_save_to_api: bool,
    scenario_keys: list[str] | None,
    api_delay_s: float,
    experiment_id: str,
    project_id: str,
    inference_delay_s: float,
    in_process: bool,
) -> tuple[list[BenchmarkResult], bool | None]:
    """Run all scenarios under one asyncio event loop."""
    return asyncio.run(
        _run_benchmarks_async(
            requests=requests,
            warmup=warmup,
            secondary_warmup=secondary_warmup,
            concurrency=concurrency,
            measurement_delay_s=measurement_delay_s,
            workload_name=workload_name,
            model_id=model_id,
            real_tracker=real_tracker,
            bootstrap_samples=bootstrap_samples,
            use_normal_ci=use_normal_ci,
            verify_logging=verify_logging,
            logging_sample=logging_sample,
            with_save_to_api=with_save_to_api,
            scenario_keys=scenario_keys,
            api_delay_s=api_delay_s,
            experiment_id=experiment_id,
            project_id=project_id,
            inference_delay_s=inference_delay_s,
            in_process=in_process,
        )
    )


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
        "--bootstrap-samples",
        type=int,
        default=BOOTSTRAP_SAMPLES,
        help="Bootstrap resamples for mean latency CI",
    )
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
        "--realistic",
        action="store_true",
        help=(
            "Live tracker + hf-embedder + uvicorn HTTP: "
            f"{REALISTIC_BENCHMARK_REQUESTS} requests, concurrency {REALISTIC_CONCURRENCY}"
        ),
    )
    parser.add_argument(
        "--no-verify-logging",
        action="store_true",
        help="Skip counting codecarbon logger lines after the default scenario",
    )
    parser.add_argument(
        "--measurement-delay-ms",
        type=float,
        default=DEFAULT_MEASUREMENT_DELAY_S * 1000,
        help="Mocked tracker stop() duration when --real-tracker is not set",
    )
    parser.add_argument(
        "--with-save-to-api",
        action="store_true",
        help="Add a scenario with save_to_api=True and api_call_interval=1",
    )
    parser.add_argument(
        "--project-id",
        default=FASTAPI_BENCHMARK_PROJECT_ID,
        help="CodeCarbon project UUID (middleware project_name for tracked scenarios)",
    )
    parser.add_argument(
        "--experiment-id",
        default=FASTAPI_BENCHMARK_EXPERIMENT_ID,
        help="CodeCarbon experiment UUID for the save_to_api scenario",
    )
    parser.add_argument(
        "--api-delay-ms",
        type=float,
        default=None,
        help="Simulated API upload latency (defaults to --measurement-delay-ms)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "Fastest run: in-process ASGI, 20 requests, skips log verify, "
            "no_logging+logging only"
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Fast run: in-process ASGI, noop + 25 ms simulated inference, "
            "50 timed requests, normal-approx CI"
        ),
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Benchmark via httpx ASGI transport (no uvicorn TCP per scenario)",
    )
    parser.add_argument(
        "--network",
        action="store_true",
        help="Force uvicorn HTTP even when --quick is set",
    )
    parser.add_argument(
        "--inference-delay-ms",
        type=float,
        default=0.0,
        help="Optional sleep per /predict request (useful with --workload noop)",
    )
    parser.add_argument(
        "--logging-sample",
        type=int,
        default=None,
        help="Verify at least N log lines (default: all requests; quick uses 10)",
    )
    parser.add_argument(
        "--scenarios",
        default=None,
        help="Comma-separated middleware scenarios: no_logging, logging, save_to_api",
    )
    args = parser.parse_args()
    if args.realistic:
        args.real_tracker = True
        args.network = True
        args.quick = False
        args.workload = "hf-embedder"
        if args.requests == BENCHMARK_REQUESTS:
            args.requests = REALISTIC_BENCHMARK_REQUESTS
        if args.warmup == WARMUP_REQUESTS:
            args.warmup = REALISTIC_WARMUP_REQUESTS
        if args.concurrency == CONCURRENCY:
            args.concurrency = REALISTIC_CONCURRENCY
        config_project, config_experiment = _config_ids()
        if args.project_id == FASTAPI_BENCHMARK_PROJECT_ID:
            args.project_id = config_project
        if args.experiment_id == FASTAPI_BENCHMARK_EXPERIMENT_ID:
            args.experiment_id = config_experiment
        os.environ.setdefault("CODECARBON_ALLOW_MULTIPLE_RUNS", "True")
    scenario_keys = (
        [part.strip() for part in args.scenarios.split(",") if part.strip()]
        if args.scenarios
        else None
    )
    use_normal_ci = False
    secondary_warmup = 0
    logging_sample = args.logging_sample
    if args.smoke:
        args.quick = True
        if args.requests == BENCHMARK_REQUESTS:
            args.requests = SMOKE_BENCHMARK_REQUESTS
        if args.warmup == WARMUP_REQUESTS:
            args.warmup = SMOKE_WARMUP_REQUESTS
        if args.inference_delay_ms == 0.0:
            args.inference_delay_ms = SMOKE_INFERENCE_DELAY_MS
        args.no_verify_logging = True
        if scenario_keys is None:
            scenario_keys = ["no_logging", "logging"]
    if args.quick:
        if args.workload == "hf-embedder":
            args.workload = "noop"
        if args.requests == BENCHMARK_REQUESTS:
            args.requests = QUICK_BENCHMARK_REQUESTS
        if args.warmup == WARMUP_REQUESTS:
            args.warmup = QUICK_WARMUP_REQUESTS
        if args.bootstrap_samples == BOOTSTRAP_SAMPLES:
            args.bootstrap_samples = QUICK_BOOTSTRAP_SAMPLES
        if args.inference_delay_ms == 0.0:
            args.inference_delay_ms = QUICK_INFERENCE_DELAY_MS
        use_normal_ci = True
        secondary_warmup = QUICK_SECONDARY_WARMUP
        if logging_sample is None and not args.no_verify_logging:
            logging_sample = QUICK_LOGGING_SAMPLE
    in_process = (args.in_process or args.quick) and not args.network
    if in_process and not args.quick and args.bootstrap_samples == BOOTSTRAP_SAMPLES:
        use_normal_ci = False
    model_id = _resolve_model_id(args.workload, args.model)
    measurement_delay_s = args.measurement_delay_ms / 1000
    api_delay_ms = (
        args.api_delay_ms
        if args.api_delay_ms is not None
        else args.measurement_delay_ms
    )
    api_delay_s = api_delay_ms / 1000
    inference_delay_s = args.inference_delay_ms / 1000

    previous_log_level = codecarbon_logger.level
    codecarbon_logger.setLevel(logging.WARNING)

    results, logging_verified = run_benchmarks(
        requests=args.requests,
        warmup=args.warmup,
        secondary_warmup=secondary_warmup,
        concurrency=args.concurrency,
        measurement_delay_s=measurement_delay_s,
        workload_name=args.workload,
        model_id=model_id,
        real_tracker=args.real_tracker,
        bootstrap_samples=args.bootstrap_samples,
        use_normal_ci=use_normal_ci,
        verify_logging=not args.no_verify_logging,
        logging_sample=logging_sample,
        with_save_to_api=args.with_save_to_api,
        scenario_keys=scenario_keys,
        api_delay_s=api_delay_s,
        experiment_id=args.experiment_id,
        project_id=args.project_id,
        inference_delay_s=inference_delay_s,
        in_process=in_process,
    )
    codecarbon_logger.setLevel(previous_log_level)
    delay_label = None if args.real_tracker else args.measurement_delay_ms
    print(
        _format_results(
            results,
            workload=args.workload,
            model_id=model_id,
            real_tracker=args.real_tracker,
            measurement_delay_ms=delay_label or 0.0,
            api_delay_ms=api_delay_ms if args.with_save_to_api else None,
            with_save_to_api=args.with_save_to_api,
            experiment_id=args.experiment_id,
            project_id=args.project_id,
            bootstrap_samples=args.bootstrap_samples,
            use_normal_ci=use_normal_ci,
            in_process=in_process,
            logging_verified=logging_verified,
        )
    )
    if logging_verified is False:
        logging_result = results[-1]
        print(
            f"\nWARNING: expected at least {logging_sample or logging_result.requests} "
            f"CodeCarbon log lines, got {logging_result.codecarbon_log_lines}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
