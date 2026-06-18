#!/usr/bin/env python3
"""
CodeCarbon measurement launch & cycle benchmark.

Measures how long it takes to START measuring (tracker init, start(), first sample)
and how much overhead each measurement cycle adds — not HTTP API throughput.

Ponytail scale: ramp workload intensity (idle → CPU spin → multi-cycle task loop)
while tracking launch time and per-cycle measurement cost.

Usage:
    uv run python scripts/benchmark_measurement.py all

    # Continuous regression loop
    uv run python scripts/benchmark_measurement.py continuous --interval 60
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = REPO_ROOT / ".context" / "measurement-benchmark-results.jsonl"

# Inline workloads (seconds) — actual code patterns, no network
WORKLOADS: dict[str, str] = {
    "idle": "import time; time.sleep({duration})",
    "cpu_light": """
import time
end = time.perf_counter() + {duration}
while time.perf_counter() < end:
    _ = sum(i * i for i in range(5000))
""",
    "cpu_heavy": """
import time
end = time.perf_counter() + {duration}
while time.perf_counter() < end:
    _ = sum(i ** 3 for i in range(50000))
""",
    "task_loop": """
import time
from codecarbon import EmissionsTracker
tracker = EmissionsTracker(
    measure_power_secs={measure_power_secs},
    output_methods=[],
    log_level="error",
    allow_multiple_runs=True,
)
tracker.start()
for i in range({rounds}):
    tracker.start_task(f"task_{{i}}")
    end = time.perf_counter() + {task_duration}
    while time.perf_counter() < end:
        _ = sum(j * j for j in range(3000))
    tracker.stop_task()
tracker.stop()
""",
}


@dataclass
class LatencyStats:
    count: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0


@dataclass
class StartupReport:
    init_ms: float
    start_ms: float
    first_measurement_ms: float
    launch_to_ready_ms: float
    offline: bool
    tracking_mode: str
    measure_power_secs: float


@dataclass
class CycleReport:
    measure_power_secs: float
    cycles_observed: int
    cycle_interval_ms: LatencyStats
    overhead_ratio: float  # mean cycle wall time / configured interval


@dataclass
class MonitorLaunchReport:
    cli_overhead_ms: float
    workload_wall_ms: float
    total_ms: float
    command: str


@dataclass
class MultiRunReport:
    runs_completed: int
    duration_s: float
    runs_per_minute: float
    cold_run_ms: float
    warm_run_ms: LatencyStats
    total_run_ms: LatencyStats


@dataclass
class ConcurrentRunsReport:
    mode: str
    workers: int
    duration_s: float
    runs_completed: int
    runs_per_minute: float
    run_latency_ms: LatencyStats


@dataclass
class BenchmarkReport:
    timestamp: str
    mode: str
    hostname: str
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


def compute_stats(values_ms: list[float]) -> LatencyStats:
    if not values_ms:
        return LatencyStats(count=0)
    s = sorted(values_ms)
    return LatencyStats(
        count=len(s),
        min_ms=s[0],
        max_ms=s[-1],
        mean_ms=statistics.mean(s),
        p50_ms=_percentile(s, 50),
        p95_ms=_percentile(s, 95),
    )


def _make_tracker(
    *,
    offline: bool,
    measure_power_secs: float,
    tracking_mode: str,
    save_to_api: bool,
):
    sys.path.insert(0, str(REPO_ROOT))
    if offline:
        from codecarbon import OfflineEmissionsTracker

        return OfflineEmissionsTracker(
            measure_power_secs=measure_power_secs,
            output_methods=[],
            log_level="error",
            allow_multiple_runs=True,
            tracking_mode=tracking_mode,
            country_iso_code="FRA",
        )
    from codecarbon import EmissionsTracker

    kwargs: dict[str, Any] = {
        "measure_power_secs": measure_power_secs,
        "output_methods": [],
        "log_level": "error",
        "allow_multiple_runs": True,
        "tracking_mode": tracking_mode,
    }
    if save_to_api:
        kwargs["output_methods"] = ["api"]
        kwargs["save_to_api"] = True
        kwargs["api_endpoint"] = os.getenv(
            "CODECARBON_API_ENDPOINT", "https://api.codecarbon.io"
        )
        kwargs["api_key"] = os.getenv("CODECARBON_API_KEY", "")
        kwargs["experiment_id"] = os.getenv(
            "CODECARBON_EXPERIMENT_ID", "5b0fa12a-3dd7-45bb-9766-cc326314d9f1"
        )
    return EmissionsTracker(**kwargs)


def benchmark_startup(
    *,
    offline: bool = True,
    measure_power_secs: float = 1.0,
    tracking_mode: str = "machine",
    save_to_api: bool = False,
    first_measurement_timeout_s: float = 30.0,
) -> StartupReport:
    """Time tracker construction, start(), and arrival of first measurement."""
    t0 = time.perf_counter()
    tracker = _make_tracker(
        offline=offline,
        measure_power_secs=measure_power_secs,
        tracking_mode=tracking_mode,
        save_to_api=save_to_api,
    )
    init_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    tracker.start()
    start_ms = (time.perf_counter() - t1) * 1000

    deadline = time.perf_counter() + first_measurement_timeout_s
    first_measurement_ms = 0.0
    while time.perf_counter() < deadline:
        if getattr(tracker, "_measure_occurrence", 0) > 0:
            first_measurement_ms = (time.perf_counter() - t0) * 1000
            break
        time.sleep(0.02)
    else:
        tracker.stop()
        raise TimeoutError(
            f"No measurement within {first_measurement_timeout_s}s "
            f"(measure_power_secs={measure_power_secs})"
        )

    tracker.stop()
    return StartupReport(
        init_ms=round(init_ms, 1),
        start_ms=round(start_ms, 1),
        first_measurement_ms=round(first_measurement_ms, 1),
        launch_to_ready_ms=round(first_measurement_ms, 1),
        offline=offline,
        tracking_mode=tracking_mode,
        measure_power_secs=measure_power_secs,
    )


def benchmark_cycles(
    *,
    measure_power_secs: float = 1.0,
    cycles_to_wait: int = 5,
    offline: bool = True,
    tracking_mode: str = "machine",
) -> CycleReport:
    """Measure wall-clock interval between consecutive measurement cycles."""
    tracker = _make_tracker(
        offline=offline,
        measure_power_secs=measure_power_secs,
        tracking_mode=tracking_mode,
        save_to_api=False,
    )
    tracker.start()

    # Wait for first cycle
    deadline = time.perf_counter() + measure_power_secs * 3
    while (
        getattr(tracker, "_measure_occurrence", 0) < 1
        and time.perf_counter() < deadline
    ):
        time.sleep(0.02)

    intervals_ms: list[float] = []
    prev = time.perf_counter()
    target = tracker._measure_occurrence + cycles_to_wait
    deadline = time.perf_counter() + measure_power_secs * (cycles_to_wait + 4)
    while tracker._measure_occurrence < target and time.perf_counter() < deadline:
        if tracker._measure_occurrence > len(intervals_ms):
            now = time.perf_counter()
            intervals_ms.append((now - prev) * 1000)
            prev = now
        time.sleep(0.01)

    tracker.stop()
    stats = compute_stats(intervals_ms)
    overhead = (
        stats.mean_ms / (measure_power_secs * 1000) if measure_power_secs else 0.0
    )
    return CycleReport(
        measure_power_secs=measure_power_secs,
        cycles_observed=len(intervals_ms),
        cycle_interval_ms=stats,
        overhead_ratio=round(overhead, 4),
    )


def _run_lifecycle_once(
    *,
    offline: bool,
    measure_power_secs: float,
    tracking_mode: str,
) -> float:
    """init → start → stop; return wall ms."""
    t0 = time.perf_counter()
    tracker = _make_tracker(
        offline=offline,
        measure_power_secs=measure_power_secs,
        tracking_mode=tracking_mode,
        save_to_api=False,
    )
    tracker.start()
    tracker.stop()
    return (time.perf_counter() - t0) * 1000


def benchmark_multi_run_same_process(
    *,
    runs: int = 20,
    offline: bool = True,
    measure_power_secs: float = 1.0,
    tracking_mode: str = "machine",
) -> MultiRunReport:
    """Repeated tracker lifecycles in one process (warm hardware cache after run 1)."""
    durations_ms: list[float] = []
    for _ in range(runs):
        durations_ms.append(
            _run_lifecycle_once(
                offline=offline,
                measure_power_secs=measure_power_secs,
                tracking_mode=tracking_mode,
            )
        )
    warm = durations_ms[1:] if len(durations_ms) > 1 else []
    total_s = sum(durations_ms) / 1000
    return MultiRunReport(
        runs_completed=len(durations_ms),
        duration_s=round(total_s, 3),
        runs_per_minute=round(len(durations_ms) / total_s * 60, 1) if total_s else 0.0,
        cold_run_ms=round(durations_ms[0], 1),
        warm_run_ms=compute_stats(warm),
        total_run_ms=compute_stats(durations_ms),
    )


def benchmark_concurrent_runs(
    *,
    duration_s: float = 60.0,
    workers: int = 8,
    offline: bool = True,
    measure_power_secs: float = 1.0,
    tracking_mode: str = "machine",
    parallel: bool = True,
) -> ConcurrentRunsReport:
    """
    How many full tracker lifecycles fit in ``duration_s``.

    parallel=True: thread pool with ``workers`` concurrent starts.
    parallel=False: sequential back-to-back runs.
    """
    mode = "parallel_threads" if parallel else "sequential"
    deadline = time.perf_counter() + duration_s
    latencies_ms: list[float] = []
    runs = 0
    lock = threading.Lock()

    if parallel:

        def worker() -> None:
            nonlocal runs
            while time.perf_counter() < deadline:
                t0 = time.perf_counter()
                tracker = _make_tracker(
                    offline=offline,
                    measure_power_secs=measure_power_secs,
                    tracking_mode=tracking_mode,
                    save_to_api=False,
                )
                tracker.start()
                tracker.stop()
                ms = (time.perf_counter() - t0) * 1000
                with lock:
                    latencies_ms.append(ms)
                    runs += 1

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(worker) for _ in range(workers)]
            for f in as_completed(futures):
                f.result()
    else:
        while time.perf_counter() < deadline:
            latencies_ms.append(
                _run_lifecycle_once(
                    offline=offline,
                    measure_power_secs=measure_power_secs,
                    tracking_mode=tracking_mode,
                )
            )
            runs += 1

    rpm = runs / duration_s * 60 if duration_s > 0 else 0.0
    return ConcurrentRunsReport(
        mode=mode,
        workers=workers if parallel else 1,
        duration_s=duration_s,
        runs_completed=runs,
        runs_per_minute=round(rpm, 1),
        run_latency_ms=compute_stats(latencies_ms),
    )


def benchmark_decorator_startup(
    measure_power_secs: float = 1.0,
    workload_duration: float = 2.0,
) -> dict[str, float]:
    """Time @track_emissions wrapper: decorator entry to first measurement."""
    sys.path.insert(0, str(REPO_ROOT))
    script = f"""
import time
from codecarbon import track_emissions

@track_emissions(
    offline=True,
    country_iso_code="FRA",
    measure_power_secs={measure_power_secs},
    output_methods=[],
    log_level="error",
    allow_multiple_runs=True,
)
def workload():
    time.sleep({workload_duration})

t0 = time.perf_counter()
workload()
print(time.perf_counter() - t0)
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=workload_duration + 60,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    total_s = (
        float(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else -1.0
    )
    return {
        "total_workload_s": round(total_s, 3),
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-300:] if proc.stderr else "",
    }


def benchmark_cli_monitor(
    *,
    workload_duration: float = 2.0,
    offline: bool = True,
    save_to_api: bool = False,
) -> MonitorLaunchReport:
    """Time `codecarbon monitor -- <workload>` launch overhead vs workload itself."""
    workload = f"import time; time.sleep({workload_duration})"
    cmd = [
        sys.executable,
        "-m",
        "codecarbon.cli.monitor_main",
        "monitor",
        "--log-level",
        "error",
        "--measure-power-secs",
        "1",
    ]
    if offline:
        cmd.extend(["--offline", "--country-iso-code", "FRA"])
    elif not save_to_api:
        cmd.append("--no-api")
    cmd.extend(["--", sys.executable, "-c", workload])

    t0 = time.perf_counter()
    subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=workload_duration + 120,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    total_ms = (time.perf_counter() - t0) * 1000
    workload_ms = workload_duration * 1000
    overhead_ms = max(0.0, total_ms - workload_ms)
    return MonitorLaunchReport(
        cli_overhead_ms=round(overhead_ms, 1),
        workload_wall_ms=round(workload_ms, 1),
        total_ms=round(total_ms, 1),
        command=" ".join(cmd),
    )


def _run_workload_subprocess(
    workload_key: str,
    *,
    duration: float,
    measure_power_secs: float,
    offline: bool,
) -> dict[str, Any]:
    """Run a tracked workload in a fresh subprocess; return parsed timings."""
    if workload_key == "task_loop":
        tracker_cls = "OfflineEmissionsTracker" if offline else "EmissionsTracker"
        offline_kw = "country_iso_code='FRA'," if offline else ""
        script = f"""
import json, time
from codecarbon import {tracker_cls}
t0 = time.perf_counter()
tracker = {tracker_cls}(
    measure_power_secs={measure_power_secs},
    output_methods=[],
    log_level="error",
    allow_multiple_runs=True,
    tracking_mode="machine",
    {offline_kw}
)
init_ms = (time.perf_counter() - t0) * 1000
t1 = time.perf_counter()
tracker.start()
start_ms = (time.perf_counter() - t1) * 1000
rounds = {max(1, int(duration))}
task_d = {max(0.5, duration / max(1, int(duration)))}
for i in range(rounds):
    tracker.start_task(f"task_{{i}}")
    end = time.perf_counter() + task_d
    while time.perf_counter() < end:
        _ = sum(j * j for j in range(3000))
    tracker.stop_task()
first_ms = None
deadline = time.perf_counter() + {measure_power_secs * 3}
while time.perf_counter() < deadline:
    if tracker._measure_occurrence > 0:
        first_ms = (time.perf_counter() - t0) * 1000
        break
    time.sleep(0.02)
tracker.stop()
print(json.dumps({{"init_ms": init_ms, "start_ms": start_ms, "first_measurement_ms": first_ms, "measure_occurrence": tracker._measure_occurrence}}))
"""
    else:
        body = WORKLOADS[workload_key].format(duration=duration)
        offline_kw = "country_iso_code='FRA'," if offline else ""
        tracker_import = "OfflineEmissionsTracker" if offline else "EmissionsTracker"
        script = f"""
import json, time
from codecarbon import {tracker_import} as TrackerCls
t0 = time.perf_counter()
tracker = TrackerCls(
    measure_power_secs={measure_power_secs},
    output_methods=[],
    log_level="error",
    allow_multiple_runs=True,
    tracking_mode="machine",
    {offline_kw}
)
init_ms = (time.perf_counter() - t0) * 1000
t1 = time.perf_counter()
tracker.start()
start_ms = (time.perf_counter() - t1) * 1000
{body}
first_ms = None
deadline = time.perf_counter() + {measure_power_secs * 3}
while time.perf_counter() < deadline:
    if tracker._measure_occurrence > 0:
        first_ms = (time.perf_counter() - t0) * 1000
        break
    time.sleep(0.02)
tracker.stop()
print(json.dumps({{"init_ms": init_ms, "start_ms": start_ms, "first_measurement_ms": first_ms, "measure_occurrence": tracker._measure_occurrence}}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=duration + 90,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    if proc.returncode != 0:
        return {"error": proc.stderr[-500:], "returncode": proc.returncode}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def benchmark_ponytail_scale(
    *,
    offline: bool = True,
    measure_power_secs: float = 1.0,
    workload_duration: float = 3.0,
) -> dict[str, Any]:
    """
    Ponytail scale: ramp workload intensity while measuring launch + first sample.
    idle → cpu_light → cpu_heavy → task_loop
    """
    steps: list[dict[str, Any]] = []
    for key in ("idle", "cpu_light", "cpu_heavy", "task_loop"):
        print(f"  workload={key} ...")
        result = _run_workload_subprocess(
            key,
            duration=workload_duration,
            measure_power_secs=measure_power_secs,
            offline=offline,
        )
        steps.append({"workload": key, **result})
        if result.get("first_measurement_ms"):
            print(
                f"    init={result.get('init_ms', 0):.0f}ms "
                f"start={result.get('start_ms', 0):.0f}ms "
                f"first_sample={result['first_measurement_ms']:.0f}ms"
            )
    return {"steps": steps, "measure_power_secs": measure_power_secs}


def benchmark_measure_interval_sweep(
    intervals: list[float],
    offline: bool = True,
) -> list[dict[str, Any]]:
    """Sweep measure_power_secs values; report launch + cycle overhead at each."""
    results = []
    for interval in intervals:
        print(f"  measure_power_secs={interval} ...")
        startup = benchmark_startup(offline=offline, measure_power_secs=interval)
        cycles = benchmark_cycles(measure_power_secs=interval, offline=offline)
        row = {
            "measure_power_secs": interval,
            "startup": asdict(startup),
            "cycles": {
                "cycles_observed": cycles.cycles_observed,
                "overhead_ratio": cycles.overhead_ratio,
                "cycle_interval_ms": asdict(cycles.cycle_interval_ms),
            },
        }
        results.append(row)
        print(
            f"    launch={startup.launch_to_ready_ms:.0f}ms "
            f"overhead={cycles.overhead_ratio:.2%}"
        )
    return results


def print_startup(label: str, s: StartupReport) -> None:
    print(
        f"  {label}: init={s.init_ms}ms start={s.start_ms}ms "
        f"first_sample={s.first_measurement_ms}ms "
        f"(mode={s.tracking_mode}, offline={s.offline})"
    )


def run_benchmarks(args: argparse.Namespace) -> BenchmarkReport:
    mode = args.mode
    results: dict[str, Any] = {}
    print(f"Measurement benchmark (mode={mode}, offline={args.offline})")

    if mode in ("startup", "all"):
        print("\n[startup] tracker init → start → first measurement")
        startup = benchmark_startup(
            offline=args.offline,
            measure_power_secs=args.measure_power_secs,
            tracking_mode=args.tracking_mode,
            save_to_api=args.with_api,
        )
        results["startup"] = asdict(startup)
        print_startup("machine tracker", startup)

        if not args.offline:
            proc_startup = benchmark_startup(
                offline=args.offline,
                measure_power_secs=args.measure_power_secs,
                tracking_mode="process",
                save_to_api=False,
            )
            results["startup_process"] = asdict(proc_startup)
            print_startup("process tracker", proc_startup)

    if mode in ("cycles", "all"):
        print(
            f"\n[cycles] {args.cycles} intervals @ measure_power_secs={args.measure_power_secs}"
        )
        cycles = benchmark_cycles(
            measure_power_secs=args.measure_power_secs,
            cycles_to_wait=args.cycles,
            offline=args.offline,
            tracking_mode=args.tracking_mode,
        )
        results["cycles"] = {
            "measure_power_secs": cycles.measure_power_secs,
            "cycles_observed": cycles.cycles_observed,
            "overhead_ratio": cycles.overhead_ratio,
            "cycle_interval_ms": asdict(cycles.cycle_interval_ms),
        }
        c = cycles.cycle_interval_ms
        print(
            f"  interval p50={c.p50_ms:.0f}ms p95={c.p95_ms:.0f}ms "
            f"overhead={cycles.overhead_ratio:.2%}"
        )

    if mode in ("cli", "all"):
        print("\n[cli] codecarbon monitor -- workload")
        cli = benchmark_cli_monitor(
            workload_duration=args.workload_duration,
            offline=args.offline,
            save_to_api=args.with_api,
        )
        results["cli_monitor"] = asdict(cli)
        print(
            f"  overhead={cli.cli_overhead_ms}ms total={cli.total_ms}ms "
            f"(workload={cli.workload_wall_ms}ms)"
        )

    if mode in ("decorator", "all"):
        print("\n[decorator] @track_emissions end-to-end")
        results["decorator"] = benchmark_decorator_startup(
            measure_power_secs=args.measure_power_secs,
            workload_duration=args.workload_duration,
        )
        print(f"  total={results['decorator']['total_workload_s']}s")

    if mode in ("ponytail", "all"):
        print("\n[ponytail scale] ramp workload intensity")
        results["ponytail"] = benchmark_ponytail_scale(
            offline=args.offline,
            measure_power_secs=args.measure_power_secs,
            workload_duration=args.workload_duration,
        )

    if mode in ("multi_run", "all"):
        print(
            f"\n[multi_run] {args.multi_run_count} sequential lifecycles (same process)"
        )
        multi = benchmark_multi_run_same_process(
            runs=args.multi_run_count,
            offline=args.offline,
            measure_power_secs=args.measure_power_secs,
            tracking_mode=args.tracking_mode,
        )
        results["multi_run"] = asdict(multi)
        w = multi.warm_run_ms
        print(
            f"  cold={multi.cold_run_ms}ms warm_p50={w.p50_ms:.0f}ms "
            f"rpm={multi.runs_per_minute:.1f}"
        )

    if mode in ("concurrent", "all"):
        print(
            f"\n[concurrent] {args.concurrent_duration}s "
            f"workers={args.concurrent_workers} parallel={not args.sequential_runs}"
        )
        concurrent = benchmark_concurrent_runs(
            duration_s=args.concurrent_duration,
            workers=args.concurrent_workers,
            offline=args.offline,
            measure_power_secs=args.measure_power_secs,
            tracking_mode=args.tracking_mode,
            parallel=not args.sequential_runs,
        )
        results["concurrent_runs"] = asdict(concurrent)
        c = concurrent.run_latency_ms
        print(
            f"  completed={concurrent.runs_completed} rpm={concurrent.runs_per_minute:.1f} "
            f"latency_p50={c.p50_ms:.0f}ms p95={c.p95_ms:.0f}ms"
        )

    if mode in ("sweep", "all"):
        intervals = [float(x) for x in args.intervals.split(",")]
        print(f"\n[interval sweep] {intervals}")
        results["interval_sweep"] = benchmark_measure_interval_sweep(
            intervals, offline=args.offline
        )

    import socket

    return BenchmarkReport(
        timestamp=_now_iso(),
        mode=mode,
        hostname=socket.gethostname(),
        results=results,
    )


def append_report(report: BenchmarkReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(asdict(report), default=str) + "\n")
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from optimization_log import record_measurement_benchmark

        record_measurement_benchmark(report.results, report.mode)
        print(f"→ updated {REPO_ROOT / '.context' / 'OPTIMIZATION_LOG.md'}")
    except Exception as exc:
        print(f"→ optimization log skipped: {exc}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CodeCarbon measurement launch benchmark")
    p.add_argument(
        "mode",
        choices=[
            "startup",
            "cycles",
            "cli",
            "decorator",
            "ponytail",
            "multi_run",
            "concurrent",
            "sweep",
            "all",
            "continuous",
        ],
    )
    p.add_argument("--offline", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument(
        "--with-api", action="store_true", help="Include API output (online only)"
    )
    p.add_argument("--measure-power-secs", type=float, default=1.0)
    p.add_argument("--tracking-mode", choices=["machine", "process"], default="machine")
    p.add_argument(
        "--cycles", type=int, default=5, help="Measurement cycles to observe"
    )
    p.add_argument("--workload-duration", type=float, default=3.0)
    p.add_argument(
        "--multi-run-count",
        type=int,
        default=20,
        help="Lifecycles for multi_run mode (same process)",
    )
    p.add_argument(
        "--concurrent-duration",
        type=float,
        default=60.0,
        help="Window (seconds) for concurrent run throughput",
    )
    p.add_argument(
        "--concurrent-workers",
        type=int,
        default=8,
        help="Parallel threads for concurrent mode",
    )
    p.add_argument(
        "--sequential-runs",
        action="store_true",
        help="Run lifecycles back-to-back instead of parallel threads",
    )
    p.add_argument(
        "--intervals",
        default="1,2,4,8,15",
        help="Comma-separated measure_power_secs values for sweep",
    )
    p.add_argument("--interval", type=float, default=60.0, help="Continuous mode sleep")
    p.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS)
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "continuous":
        print(
            f"Continuous measurement benchmark every {args.interval}s → {args.results_file}"
        )
        try:
            while True:
                report = run_benchmarks(
                    argparse.Namespace(**{**vars(args), "mode": "all"})
                )
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
