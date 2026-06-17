#!/usr/bin/env python3
"""
CodeCarbon API speed benchmark harness.

Measures startup time, endpoint latency, and throughput using the ponytail scale:
concurrency ramps 1 → 2 → 4 → 8 → … until error rate or latency SLO is exceeded.

Usage:
    export CODECARBON_API_URL=http://localhost:8008
    uv run python scripts/benchmark_codecarbon_api.py all --bootstrap

    # Continuous regression loop
    uv run python scripts/benchmark_codecarbon_api.py continuous --bootstrap --interval 60
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = REPO_ROOT / ".context" / "benchmark-results.jsonl"
MAIN_USER_ID = "bb479cc8-3357-4859-985d-e3cc209d6fc9"


@dataclass
class LatencyStats:
    count: int = 0
    errors: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    throughput_rps: float = 0.0


@dataclass
class BenchmarkFixture:
    api_url: str
    api_base: str
    project_token: str
    experiment_id: str
    jwt_token: Optional[str] = None
    org_id: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class BenchmarkReport:
    timestamp: str
    api_url: str
    mode: str
    results: dict[str, Any] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def compute_stats(latencies_ms: list[float], errors: int, duration_s: float) -> LatencyStats:
    if not latencies_ms:
        return LatencyStats(count=0, errors=errors)
    sorted_lat = sorted(latencies_ms)
    ok = len(sorted_lat)
    return LatencyStats(
        count=ok,
        errors=errors,
        min_ms=sorted_lat[0],
        max_ms=sorted_lat[-1],
        mean_ms=statistics.mean(sorted_lat),
        p50_ms=_percentile(sorted_lat, 50),
        p95_ms=_percentile(sorted_lat, 95),
        p99_ms=_percentile(sorted_lat, 99),
        throughput_rps=ok / duration_s if duration_s > 0 else 0.0,
    )


def normalize_api_url(url: str) -> tuple[str, str]:
    """Return (root_url, api_base) where api_base includes /api."""
    root = url.rstrip("/")
    if root.endswith("/api"):
        return root[: -len("/api")], root
    return root, root + "/api"


def _jwt_headers(jwt_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def bootstrap_fixture(api_url: str, jwt_key: str) -> BenchmarkFixture:
    """Create ephemeral org/project/experiment/token for benchmarking."""
    try:
        import jwt
    except ImportError as exc:
        raise SystemExit("Install PyJWT: uv sync --project carbonserver --extra dev") from exc

    root, api_base = normalize_api_url(api_url)
    jwt_token = jwt.encode({"sub": MAIN_USER_ID}, key=jwt_key, algorithm="HS256")
    session = requests.Session()
    session.headers.update(_jwt_headers(jwt_token))

    suffix = uuid.uuid4().hex[:8]
    org_payload = {"name": f"bench_org_{suffix}", "description": "API benchmark fixture"}
    org_resp = session.post(f"{api_base}/organizations", json=org_payload, timeout=10)
    org_resp.raise_for_status()
    org_id = org_resp.json()["id"]

    project_payload = {
        "name": f"bench_project_{suffix}",
        "description": "API benchmark fixture",
        "organization_id": org_id,
    }
    project_resp = session.post(f"{api_base}/projects/", json=project_payload, timeout=10)
    project_resp.raise_for_status()
    project_id = project_resp.json()["id"]

    experiment_payload = {
        "name": f"bench_experiment_{suffix}",
        "description": "API benchmark fixture",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "country_name": "France",
        "country_iso_code": "FRA",
        "region": "france",
        "on_cloud": True,
        "cloud_provider": "Premise",
        "cloud_region": "eu-west-1a",
        "project_id": project_id,
    }
    exp_resp = session.post(f"{api_base}/experiments", json=experiment_payload, timeout=10)
    exp_resp.raise_for_status()
    experiment_id = exp_resp.json()["id"]

    token_payload = {"name": f"bench_token_{suffix}", "access": 2}
    token_resp = session.post(
        f"{api_base}/projects/{project_id}/api-tokens", json=token_payload, timeout=10
    )
    token_resp.raise_for_status()
    project_token = token_resp.json()["token"]

    return BenchmarkFixture(
        api_url=root,
        api_base=api_base,
        project_token=project_token,
        experiment_id=experiment_id,
        jwt_token=jwt_token,
        org_id=org_id,
        project_id=project_id,
    )


def load_fixture(args: argparse.Namespace) -> BenchmarkFixture:
    api_url = args.api_url or os.getenv("CODECARBON_API_URL", "http://localhost:8008")
    root, api_base = normalize_api_url(api_url)

    token = args.api_token or os.getenv("CODECARBON_API_TOKEN")
    experiment_id = args.experiment_id or os.getenv("CODECARBON_EXPERIMENT_ID")

    if token and experiment_id:
        return BenchmarkFixture(
            api_url=root,
            api_base=api_base,
            project_token=token,
            experiment_id=experiment_id,
        )

    if args.bootstrap:
        jwt_key = args.jwt_key or os.getenv("JWT_KEY", "")
        if not jwt_key:
            raise SystemExit(
                "Bootstrap requires JWT_KEY (or pass --jwt-key). "
                "Set ENVIRONMENT=local and run initial_data.py first."
            )
        return bootstrap_fixture(api_url, jwt_key)

    raise SystemExit(
        "Provide CODECARBON_API_TOKEN + CODECARBON_EXPERIMENT_ID, or use --bootstrap."
    )


def run_payload_factory(fixture: BenchmarkFixture) -> tuple[dict, dict]:
    run_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiment_id": fixture.experiment_id,
        "os": "benchmark-os",
        "python_version": "3.12.0",
        "codecarbon_version": "3.2.8",
        "cpu_count": 8,
        "cpu_model": "Benchmark CPU",
        "gpu_count": 0,
        "gpu_model": "None",
        "longitude": 2.3,
        "latitude": 48.8,
        "region": "EUROPE",
        "provider": "benchmark",
        "ram_total_size": 16384.0,
        "tracking_mode": "Machine",
    }
    emission_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": "",
        "duration": 10,
        "emissions_sum": 0.001,
        "emissions_rate": 0.0001,
        "cpu_power": 25.0,
        "gpu_power": 0.0,
        "ram_power": 5.0,
        "cpu_energy": 0.00007,
        "gpu_energy": 0.0,
        "ram_energy": 0.00001,
        "energy_consumed": 0.00008,
        "wue": 0,
    }
    return run_payload, emission_payload


def _timed_request(fn: Callable[[], requests.Response]) -> tuple[float, Optional[int]]:
    start = time.perf_counter()
    try:
        resp = fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        if resp.status_code >= 400:
            return elapsed_ms, resp.status_code
        return elapsed_ms, None
    except requests.RequestException:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, -1


def benchmark_health(fixture: BenchmarkFixture, iterations: int) -> LatencyStats:
    latencies: list[float] = []
    errors = 0
    start = time.perf_counter()
    session = requests.Session()
    for _ in range(iterations):
        ms, err = _timed_request(lambda: session.get(f"{fixture.api_url}/", timeout=10))
        latencies.append(ms)
        if err is not None:
            errors += 1
    return compute_stats(latencies, errors, time.perf_counter() - start)


def benchmark_write_path(fixture: BenchmarkFixture, iterations: int) -> dict[str, LatencyStats]:
    """Measure POST /runs and POST /emissions latency (sequential)."""
    run_payload, emission_payload = run_payload_factory(fixture)
    run_latencies: list[float] = []
    emission_latencies: list[float] = []
    run_errors = emission_errors = 0
    start = time.perf_counter()
    session = requests.Session()
    headers = {"x-api-token": fixture.project_token, "Content-Type": "application/json"}

    for _ in range(iterations):
        run_response: dict[str, requests.Response] = {}

        def post_run() -> requests.Response:
            resp = session.post(
                f"{fixture.api_base}/runs/", json=run_payload, headers=headers, timeout=10
            )
            run_response["resp"] = resp
            return resp

        ms, err = _timed_request(post_run)
        run_latencies.append(ms)
        if err is not None:
            run_errors += 1
            continue
        run_id = run_response["resp"].json()["id"]

        payload = {**emission_payload, "run_id": run_id, "timestamp": _now_iso()}
        ms, err = _timed_request(
            lambda p=payload: session.post(
                f"{fixture.api_base}/emissions/", json=p, headers=headers, timeout=10
            )
        )
        emission_latencies.append(ms)
        if err is not None:
            emission_errors += 1

    duration = time.perf_counter() - start
    return {
        "post_runs": compute_stats(run_latencies, run_errors, duration),
        "post_emissions": compute_stats(emission_latencies, emission_errors, duration),
    }


def _emission_worker(fixture: BenchmarkFixture, worker_id: int) -> tuple[float, Optional[int]]:
    """Single write-path request: create run + post emission."""
    run_payload, emission_payload = run_payload_factory(fixture)
    run_payload["cpu_model"] = f"Benchmark CPU worker-{worker_id}"
    headers = {"x-api-token": fixture.project_token, "Content-Type": "application/json"}
    session = requests.Session()
    start = time.perf_counter()
    try:
        run_resp = session.post(
            f"{fixture.api_base}/runs/", json=run_payload, headers=headers, timeout=30
        )
        if run_resp.status_code >= 400:
            return (time.perf_counter() - start) * 1000, run_resp.status_code
        run_id = run_resp.json()["id"]
        payload = {**emission_payload, "run_id": run_id, "timestamp": _now_iso()}
        em_resp = session.post(
            f"{fixture.api_base}/emissions/", json=payload, headers=headers, timeout=30
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        if em_resp.status_code >= 400:
            return elapsed_ms, em_resp.status_code
        return elapsed_ms, None
    except requests.RequestException:
        return (time.perf_counter() - start) * 1000, -1


def benchmark_ponytail_scale(
    fixture: BenchmarkFixture,
    max_concurrency: int,
    requests_per_step: int,
    slo_ms: float,
    error_rate_limit: float,
) -> dict[str, Any]:
    """
    Ponytail scale: ramp concurrency 1 → 2 → 4 → 8 → … mapping the performance curve.
    Stops when p95 exceeds slo_ms or error rate exceeds error_rate_limit.
    """
    steps: list[dict[str, Any]] = []
    concurrency = 1
    while concurrency <= max_concurrency:
        latencies: list[float] = []
        errors = 0
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [
                pool.submit(_emission_worker, fixture, i % concurrency)
                for i in range(requests_per_step)
            ]
            for fut in as_completed(futures):
                ms, err = fut.result()
                latencies.append(ms)
                if err is not None:
                    errors += 1
        duration = time.perf_counter() - start
        stats = compute_stats(latencies, errors, duration)
        total = stats.count + stats.errors
        error_rate = stats.errors / total if total else 0.0
        step = {
            "concurrency": concurrency,
            "stats": asdict(stats),
            "error_rate": round(error_rate, 4),
        }
        steps.append(step)
        print(
            f"  ponytail c={concurrency}: p50={stats.p50_ms:.1f}ms "
            f"p95={stats.p95_ms:.1f}ms rps={stats.throughput_rps:.1f} "
            f"errors={stats.errors}/{total}"
        )
        if stats.p95_ms > slo_ms or error_rate > error_rate_limit:
            step["stopped_reason"] = (
                "p95_slo" if stats.p95_ms > slo_ms else "error_rate"
            )
            break
        concurrency *= 2

    peak = max(steps, key=lambda s: s["stats"]["throughput_rps"]) if steps else None
    return {"steps": steps, "peak_throughput_step": peak}


def wait_for_health(url: str, timeout_s: float, poll_interval_s: float = 0.25) -> float:
    """Poll GET / until OK or timeout. Returns seconds until ready."""
    start = time.perf_counter()
    deadline = start + timeout_s
    while time.perf_counter() < deadline:
        try:
            resp = requests.get(f"{url.rstrip('/')}/", timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "OK":
                return time.perf_counter() - start
        except (requests.RequestException, ValueError):
            pass
        time.sleep(poll_interval_s)
    raise TimeoutError(f"API not ready at {url} after {timeout_s}s")


def benchmark_startup(
    api_url: str,
    launch_server: bool,
    startup_timeout_s: float,
) -> dict[str, Any]:
    """Measure cold-start time until health check passes."""
    root, _ = normalize_api_url(api_url)
    result: dict[str, Any] = {"api_url": root}

    if launch_server:
        env = os.environ.copy()
        env.setdefault("DATABASE_URL", "postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db")
        proc = subprocess.Popen(
            ["uv", "run", "--project", "carbonserver", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"],
            cwd=str(REPO_ROOT / "carbonserver"),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        result["launch_command"] = "uvicorn main:app --port 8008"
        start = time.perf_counter()
        try:
            wait_for_health(root, startup_timeout_s)
            result["startup_ms"] = round((time.perf_counter() - start) * 1000, 1)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    else:
        start = time.perf_counter()
        try:
            wait_for_health(root, startup_timeout_s)
            result["health_ready_ms"] = round((time.perf_counter() - start) * 1000, 1)
        except TimeoutError as exc:
            result["error"] = str(exc)

    return result


def benchmark_client_startup(fixture: BenchmarkFixture, iterations: int) -> LatencyStats:
    """Measure ApiClient construction + automatic run registration."""
    sys.path.insert(0, str(REPO_ROOT))
    from codecarbon.core.api_client import ApiClient

    latencies: list[float] = []
    errors = 0
    conf = {
        "os": "benchmark-os",
        "python_version": "3.12.0",
        "codecarbon_version": "3.2.8",
        "cpu_count": 4,
        "cpu_model": "Benchmark",
        "gpu_count": 0,
        "gpu_model": "None",
        "longitude": 2.3,
        "latitude": 48.8,
        "region": "EUROPE",
        "provider": "benchmark",
        "ram_total_size": 8192.0,
        "tracking_mode": "Machine",
    }
    start = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            client = ApiClient(
                endpoint_url=fixture.api_base,
                experiment_id=fixture.experiment_id,
                api_key=fixture.project_token,
                conf=conf,
                create_run_automatically=True,
            )
            if client.run_id is None:
                errors += 1
            latencies.append((time.perf_counter() - t0) * 1000)
        except Exception:
            errors += 1
            latencies.append((time.perf_counter() - t0) * 1000)
    return compute_stats(latencies, errors, time.perf_counter() - start)


def benchmark_client_workload(
    fixture: BenchmarkFixture,
    duration_s: float,
    measure_power_secs: float,
) -> dict[str, Any]:
    """
    Run a minimal tracked workload (actual codecarbon package) and measure
    time-to-first-emission-upload.
    """
    script = f"""
import os
import time
os.environ["CODECARBON_API_ENDPOINT"] = {fixture.api_base!r}
from codecarbon import EmissionsTracker
from codecarbon.output_methods.base_output import OutputMethod

tracker = EmissionsTracker(
    project_name="api_benchmark",
    measure_power_secs={measure_power_secs},
    api_call_interval=1,
    output_methods=[OutputMethod.API],
    api_endpoint={fixture.api_base!r},
    api_key={fixture.project_token!r},
    experiment_id={fixture.experiment_id!r},
    log_level="error",
    allow_multiple_runs=True,
)
start = time.perf_counter()
tracker.start()
time.sleep({max(measure_power_secs + 1, 2)!r})
tracker.flush()
first_upload_ms = (time.perf_counter() - start) * 1000
tracker.stop()
print(first_upload_ms)
"""
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=duration_s + 30,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    wall_ms = (time.perf_counter() - start) * 1000
    first_upload_ms = None
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            first_upload_ms = float(proc.stdout.strip().splitlines()[-1])
        except ValueError:
            pass
    return {
        "wall_ms": round(wall_ms, 1),
        "first_upload_ms": round(first_upload_ms, 1) if first_upload_ms else None,
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
    }


def stats_to_dict(obj: Any) -> Any:
    if isinstance(obj, LatencyStats):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: stats_to_dict(v) for k, v in obj.items()}
    return obj


def print_stats(label: str, stats: LatencyStats) -> None:
    print(
        f"  {label}: n={stats.count} err={stats.errors} "
        f"p50={stats.p50_ms:.1f}ms p95={stats.p95_ms:.1f}ms "
        f"rps={stats.throughput_rps:.1f}"
    )


def _needs_fixture(mode: str) -> bool:
    return mode in (
        "write",
        "ponytail",
        "throughput",
        "client",
        "all",
        "continuous",
        "latency",
    )


def run_benchmarks(args: argparse.Namespace) -> BenchmarkReport:
    mode = args.mode
    api_url = args.api_url or os.getenv("CODECARBON_API_URL", "http://localhost:8008")
    root, _ = normalize_api_url(api_url)
    results: dict[str, Any] = {}

    fixture: Optional[BenchmarkFixture] = None
    if _needs_fixture(mode):
        fixture = load_fixture(args)

    target = fixture.api_url if fixture else root
    print(f"Benchmark target: {target} (mode={mode})")

    if mode in ("startup", "all"):
        print("\n[startup]")
        results["startup"] = benchmark_startup(root, args.launch_server, args.startup_timeout)
        for k, v in results["startup"].items():
            print(f"  {k}: {v}")

    if mode in ("health", "latency", "all"):
        print(f"\n[health] ({args.iterations} iterations)")
        health = benchmark_health(
            fixture
            or BenchmarkFixture(
                api_url=root, api_base=root + "/api", project_token="", experiment_id=""
            ),
            args.iterations,
        )
        results["health"] = asdict(health)
        print_stats("GET /", health)

    if fixture and mode in ("write", "latency", "all"):
        print(f"\n[write path] ({args.iterations} iterations)")
        write = benchmark_write_path(fixture, args.iterations)
        results["write_path"] = stats_to_dict(write)
        print_stats("POST /runs", write["post_runs"])
        print_stats("POST /emissions", write["post_emissions"])

    if fixture and mode in ("ponytail", "throughput", "all"):
        print(
            f"\n[ponytail scale] max_c={args.max_concurrency} "
            f"req/step={args.requests_per_step} slo={args.slo_ms}ms"
        )
        results["ponytail"] = benchmark_ponytail_scale(
            fixture,
            args.max_concurrency,
            args.requests_per_step,
            args.slo_ms,
            args.error_rate_limit,
        )

    if fixture and mode in ("client", "all"):
        print(f"\n[client startup] ({args.iterations} iterations)")
        client_stats = benchmark_client_startup(fixture, min(args.iterations, 5))
        results["client_startup"] = asdict(client_stats)
        print_stats("ApiClient init+run", client_stats)

        print("\n[client workload] (tracked subprocess)")
        results["client_workload"] = benchmark_client_workload(
            fixture, args.workload_duration, args.measure_power_secs
        )
        cw = results["client_workload"]
        print(f"  first_upload_ms: {cw.get('first_upload_ms')} wall_ms: {cw.get('wall_ms')}")

    return BenchmarkReport(
        timestamp=_now_iso(),
        api_url=target,
        mode=mode,
        results=results,
    )


def append_report(report: BenchmarkReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(asdict(report), default=str) + "\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CodeCarbon API speed benchmark")
    p.add_argument(
        "mode",
        choices=["startup", "health", "write", "latency", "ponytail", "throughput", "client", "all", "continuous"],
        help="Benchmark mode (continuous = loop all)",
    )
    p.add_argument("--api-url", default=None, help="API root URL (default: CODECARBON_API_URL)")
    p.add_argument("--api-token", default=None, help="Project API token (x-api-token)")
    p.add_argument("--experiment-id", default=None, help="Experiment UUID for write tests")
    p.add_argument("--bootstrap", action="store_true", help="Create ephemeral test fixtures via JWT")
    p.add_argument("--jwt-key", default=None, help="JWT signing key for bootstrap")
    p.add_argument("--iterations", type=int, default=20, help="Requests per latency benchmark")
    p.add_argument("--max-concurrency", type=int, default=32, help="Ponytail max concurrent workers")
    p.add_argument("--requests-per-step", type=int, default=40, help="Total requests per ponytail step")
    p.add_argument("--slo-ms", type=float, default=2000.0, help="Stop ponytail when p95 exceeds this")
    p.add_argument("--error-rate-limit", type=float, default=0.05, help="Stop ponytail when errors exceed ratio")
    p.add_argument("--startup-timeout", type=float, default=60.0, help="Seconds to wait for API health")
    p.add_argument("--launch-server", action="store_true", help="Spawn uvicorn and measure cold start")
    p.add_argument("--workload-duration", type=float, default=10.0, help="Client workload max seconds")
    p.add_argument("--measure-power-secs", type=float, default=1.0, help="Tracker measure interval for client test")
    p.add_argument("--interval", type=float, default=60.0, help="Seconds between continuous runs")
    p.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS, help="JSONL output path")
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "continuous":
        print(f"Continuous benchmark every {args.interval}s → {args.results_file}")
        print("Press Ctrl+C to stop.\n")
        try:
            while True:
                report = run_benchmarks(argparse.Namespace(**{**vars(args), "mode": "all"}))
                append_report(report, args.results_file)
                print(f"\n→ appended to {args.results_file}\n")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        report = run_benchmarks(args)
        append_report(report, args.results_file)
        print(f"\n→ results appended to {args.results_file}")


if __name__ == "__main__":
    main()
