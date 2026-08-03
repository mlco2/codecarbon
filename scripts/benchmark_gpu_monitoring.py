#!/usr/bin/env python3
"""
Benchmark: GPU monitoring overhead — heavyweight get_gpu_details vs lightweight get_gpu_utilization_list.

Measures how many unnecessary NVML calls the per-second _monitor_power() hot path
makes on multi-GPU systems, and the latency difference between the old full-detail
path and the new lightweight utilization-only path.

Usage:
    # Quick run (default)
    uv run python scripts/benchmark_gpu_monitoring.py

    # Full benchmark with subprocess cold-start samples
    uv run python scripts/benchmark_gpu_monitoring.py all

    # Simulated multi-GPU scale (no real GPU needed)
    uv run python scripts/benchmark_gpu_monitoring.py all --simulate-gpus 8

Methodology:
    - Cold metrics: spawn fresh Python subprocesses, each performing full GPU init
    - Warm metrics: repeat calls in the same process after warm-up
    - p50 (median) reported across multiple samples
    - NVML call counts derived from source code audit (gpu_nvidia.py + gpu_device.py)
    - On real NVIDIA hardware: wall-clock timing of actual NVML calls
    - On non-NVIDIA hardware: mock NVML with realistic simulated call latencies
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / ".context"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_RESULTS = RESULTS_DIR / "gpu-benchmark-results.jsonl"

# NVML call categories based on source audit (gpu_nvidia.py + gpu_device.py)
# _monitor_power() calls get_gpu_details() every 1s but only uses gpu_utilization
NVML_CALLS_HEAVY = [
    "nvmlDeviceGetMemoryInfo",  # → free_memory, total_memory, used_memory  — DISCARDED
    "nvmlDeviceGetTemperature",  # → temperature                              — DISCARDED
    "nvmlDeviceGetPowerUsage",  # → power_usage                              — DISCARDED
    "nvmlDeviceGetTotalEnergyConsumption",  # → total_energy_consumption            — DISCARDED
    "nvmlDeviceGetUtilizationRates",  # → gpu_utilization                          — USED
    "nvmlDeviceGetComputeMode",  # → compute_mode                             — DISCARDED
    "nvmlDeviceGetComputeRunningProcesses",  # → compute_processes                  — DISCARDED (most expensive)
    "nvmlDeviceGetGraphicsRunningProcesses",  # → graphics_processes                — DISCARDED (most expensive)
]

NVML_CALLS_LIGHTWEIGHT = [
    "nvmlDeviceGetUtilizationRates",  # ← the only call we need for utilization
]

# Simulated per-call latencies (microseconds) for non-GPU systems.
# Based on typical NVML overheads reported in NVIDIA docs & community benchmarks.
# Process enumeration (GetComputeRunningProcesses) is the most expensive because
# it iterates active GPU processes and collects PID-level info.
SIMULATED_LATENCY_US: dict[str, float] = {
    "nvmlDeviceGetMemoryInfo": 50,
    "nvmlDeviceGetTemperature": 40,
    "nvmlDeviceGetPowerUsage": 45,
    "nvmlDeviceGetTotalEnergyConsumption": 40,
    "nvmlDeviceGetUtilizationRates": 50,
    "nvmlDeviceGetComputeMode": 35,
    "nvmlDeviceGetComputeRunningProcesses": 500,  # ← expensive: process enumeration
    "nvmlDeviceGetGraphicsRunningProcesses": 500,  # ← expensive: process enumeration
    "nvmlDeviceGetName": 40,
    "nvmlDeviceGetUUID": 35,
    "nvmlDeviceGetEnforcedPowerLimit": 40,
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
class NvmlCallBreakdown:
    call_name: str
    latency_us: float
    used_by_monitor: bool


@dataclass
class GpuDetailMethodBenchmark:
    method: str  # "get_gpu_details" or "get_gpu_utilization_list"
    gpu_count: int
    nvml_calls_per_second: int
    nvml_calls_unused_per_second: int
    latency_per_call_ms: LatencyStats
    latency_per_second_ms: float  # projected = per_gpu * gpu_count


@dataclass
class MonitoringOverheadProjection:
    metric: str
    heavy_path: float
    lightweight_path: float
    savings: float
    unit: str


@dataclass
class BenchmarkReport:
    timestamp: str
    mode: str
    hostname: str
    gpu_backend: str
    gpu_count_real: int
    simulated: bool
    call_breakdown: list[dict]
    method_benchmarks: list[dict]
    projections: list[dict]
    result: str = ""


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


def _detect_gpu_backend() -> tuple[str, int]:
    """Detect real GPU backend and count. Returns (backend_name, count)."""
    try:
        from codecarbon.core.gpu import AMDSMI_AVAILABLE, PYNVML_AVAILABLE

        if PYNVML_AVAILABLE:
            from codecarbon.core import gpu_nvidia

            count = gpu_nvidia.pynvml.nvmlDeviceGetCount()
            return ("nvidia", count)
        if AMDSMI_AVAILABLE:
            return ("amd", 0)  # count not trivial
    except Exception:
        pass
    return ("none", 0)


def _collect_call_breakdown() -> list[dict]:
    """Return the per-NVML-call breakdown showing what's used vs discarded."""
    results = []
    for call in NVML_CALLS_HEAVY:
        results.append(
            {
                "call_name": call,
                "used_by_monitor": call == "nvmlDeviceGetUtilizationRates",
                "simulated_latency_us": SIMULATED_LATENCY_US.get(call, 50),
            }
        )
    return results


def _mock_time_for_call(call_name: str) -> None:
    """Sleep to simulate NVML call latency when no real GPU is available."""
    time.sleep(SIMULATED_LATENCY_US.get(call_name, 50) / 1_000_000)


class MockNvidiaGPUDevice:
    """A lightweight mock that simulates NVML call latencies.

    Used on non-NVIDIA systems so the benchmark can still measure
    relative overhead and project multi-GPU scaling.
    """

    def __init__(self, gpu_index: int):
        self.gpu_index = gpu_index

    def get_gpu_details(self) -> dict:
        _mock_time_for_call("nvmlDeviceGetMemoryInfo")
        _mock_time_for_call("nvmlDeviceGetTemperature")
        _mock_time_for_call("nvmlDeviceGetPowerUsage")
        _mock_time_for_call("nvmlDeviceGetTotalEnergyConsumption")
        _mock_time_for_call("nvmlDeviceGetUtilizationRates")
        _mock_time_for_call("nvmlDeviceGetComputeMode")
        _mock_time_for_call("nvmlDeviceGetComputeRunningProcesses")
        _mock_time_for_call("nvmlDeviceGetGraphicsRunningProcesses")
        return {"gpu_index": self.gpu_index, "gpu_utilization": 50}

    def get_gpu_utilization_lightweight(self) -> dict:
        _mock_time_for_call("nvmlDeviceGetUtilizationRates")
        return {"gpu_index": self.gpu_index, "gpu_utilization": 50}


def _benchmark_method(
    devices: list,
    method_name: str,
    samples: int = 200,
    warmup: int = 20,
) -> LatencyStats:
    """Benchmark a GPU method. Returns latency stats in milliseconds."""
    for _ in range(warmup):
        if method_name == "get_gpu_details":
            [d.get_gpu_details() for d in devices]
        else:
            [d.get_gpu_utilization_lightweight() for d in devices]

    timings = []
    for _ in range(samples):
        t0 = time.perf_counter()
        if method_name == "get_gpu_details":
            [d.get_gpu_details() for d in devices]
        else:
            [d.get_gpu_utilization_lightweight() for d in devices]
        elapsed_ms = (time.perf_counter() - t0) * 1000
        timings.append(elapsed_ms)

    return compute_stats(timings)


def _benchmark_real_gpu(gpu_count: int) -> tuple[list[dict], list[dict]]:
    """Benchmark using real GPU hardware via AllGPUDevices."""
    sys.path.insert(0, str(REPO_ROOT))
    from codecarbon.core.gpu import AllGPUDevices

    devices = AllGPUDevices()
    actual_count = devices.device_count

    heavy_stats = _benchmark_method(devices.devices, "get_gpu_details")
    light_stats = _benchmark_method(devices.devices, "get_gpu_utilization_lightweight")

    method_benchmarks = [
        {
            "method": "get_gpu_details",
            "gpu_count": actual_count,
            "nvml_calls_per_second": len(NVML_CALLS_HEAVY) * actual_count,
            "nvml_calls_unused_per_second": (len(NVML_CALLS_HEAVY) - 1) * actual_count,
            "latency_per_call_ms": asdict(heavy_stats),
            "latency_per_second_ms": heavy_stats.p50_ms,
        },
        {
            "method": "get_gpu_utilization_list",
            "gpu_count": actual_count,
            "nvml_calls_per_second": len(NVML_CALLS_LIGHTWEIGHT) * actual_count,
            "nvml_calls_unused_per_second": 0,
            "latency_per_call_ms": asdict(light_stats),
            "latency_per_second_ms": light_stats.p50_ms,
        },
    ]

    # Scale projections for multi-GPU
    for simulated_count in [1, 4, 8]:
        scale = simulated_count / actual_count if actual_count else 1
        method_benchmarks.append(
            {
                "method": f"get_gpu_details (projected {simulated_count} GPU)",
                "gpu_count": simulated_count,
                "nvml_calls_per_second": len(NVML_CALLS_HEAVY) * simulated_count,
                "nvml_calls_unused_per_second": (len(NVML_CALLS_HEAVY) - 1)
                * simulated_count,
                "latency_per_call_ms": asdict(heavy_stats),
                "latency_per_second_ms": heavy_stats.p50_ms * scale,
            }
        )
        method_benchmarks.append(
            {
                "method": f"get_gpu_utilization_list (projected {simulated_count} GPU)",
                "gpu_count": simulated_count,
                "nvml_calls_per_second": len(NVML_CALLS_LIGHTWEIGHT) * simulated_count,
                "nvml_calls_unused_per_second": 0,
                "latency_per_call_ms": asdict(light_stats),
                "latency_per_second_ms": light_stats.p50_ms * scale,
            }
        )

    return method_benchmarks, []


def _benchmark_simulated_gpu(simulate_gpus: int) -> tuple[list[dict], list[dict]]:
    """Benchmark using mock devices with simulated NVML latencies."""
    devices = [MockNvidiaGPUDevice(i) for i in range(simulate_gpus)]

    heavy_stats = _benchmark_method(devices, "get_gpu_details")
    light_stats = _benchmark_method(devices, "get_gpu_utilization_lightweight")

    method_benchmarks = [
        {
            "method": "get_gpu_details",
            "gpu_count": simulate_gpus,
            "nvml_calls_per_second": len(NVML_CALLS_HEAVY) * simulate_gpus,
            "nvml_calls_unused_per_second": (len(NVML_CALLS_HEAVY) - 1) * simulate_gpus,
            "latency_per_call_ms": asdict(heavy_stats),
            "latency_per_second_ms": heavy_stats.p50_ms,
        },
        {
            "method": "get_gpu_utilization_list",
            "gpu_count": simulate_gpus,
            "nvml_calls_per_second": len(NVML_CALLS_LIGHTWEIGHT) * simulate_gpus,
            "nvml_calls_unused_per_second": 0,
            "latency_per_call_ms": asdict(light_stats),
            "latency_per_second_ms": light_stats.p50_ms,
        },
    ]

    return method_benchmarks, []


def _compute_projections(method_benchmarks: list[dict]) -> list[dict]:
    """Compute time-savings projections from benchmark results."""
    heavy = next(
        (m for m in method_benchmarks if m["method"] == "get_gpu_details"), None
    )
    light = next(
        (m for m in method_benchmarks if m["method"] == "get_gpu_utilization_list"),
        None,
    )
    if not heavy or not light:
        return []

    heavy_per_sec = heavy["latency_per_second_ms"]
    light_per_sec = light["latency_per_second_ms"]
    savings_per_sec = heavy_per_sec - light_per_sec

    gpu_count = heavy["gpu_count"]

    return [
        {
            "metric": "Per-second monitoring overhead",
            "heavy_path_ms": heavy_per_sec,
            "lightweight_path_ms": light_per_sec,
            "savings_ms": savings_per_sec,
            "savings_pct": (
                round((savings_per_sec / heavy_per_sec) * 100, 1)
                if heavy_per_sec
                else 0
            ),
            "unit": "ms/s",
        },
        {
            "metric": "Per-minute monitoring overhead",
            "heavy_path_ms": heavy_per_sec * 60,
            "lightweight_path_ms": light_per_sec * 60,
            "savings_ms": savings_per_sec * 60,
            "savings_pct": (
                round((savings_per_sec / heavy_per_sec) * 100, 1)
                if heavy_per_sec
                else 0
            ),
            "unit": "ms/min",
        },
        {
            "metric": "Per-hour monitoring overhead",
            "heavy_path_ms": heavy_per_sec * 3600,
            "lightweight_path_ms": light_per_sec * 3600,
            "savings_ms": savings_per_sec * 3600,
            "savings_pct": (
                round((savings_per_sec / heavy_per_sec) * 100, 1)
                if heavy_per_sec
                else 0
            ),
            "unit": "ms/hr",
        },
        {
            "metric": "Per-day monitoring overhead (24h)",
            "heavy_path_ms": heavy_per_sec * 86400,
            "lightweight_path_ms": light_per_sec * 86400,
            "savings_ms": savings_per_sec * 86400,
            "savings_pct": (
                round((savings_per_sec / heavy_per_sec) * 100, 1)
                if heavy_per_sec
                else 0
            ),
            "unit": "ms/day",
        },
        {
            "metric": "Unnecessary NVML calls per second",
            "heavy_path_value": heavy["nvml_calls_unused_per_second"],
            "lightweight_path_value": 0,
            "savings_value": heavy["nvml_calls_unused_per_second"],
            "unit": "calls/s",
        },
        {
            "metric": f"Unnecessary NVML calls per hour (on {gpu_count} GPU{'s' if gpu_count != 1 else ''})",
            "heavy_path_value": heavy["nvml_calls_unused_per_second"] * 3600,
            "lightweight_path_value": 0,
            "savings_value": heavy["nvml_calls_unused_per_second"] * 3600,
            "unit": "calls/hr",
        },
    ]


def run_all(simulate_gpus: int | None = None) -> BenchmarkReport:
    backend, real_count = _detect_gpu_backend()
    simulated = backend == "none" and simulate_gpus is not None

    if backend != "none" and real_count > 0:
        gpu_backend = f"nvidia ({real_count} GPU{'s' if real_count != 1 else ''})"
        method_bms, _ = _benchmark_real_gpu(real_count)
    elif simulate_gpus:
        gpu_backend = (
            f"simulated ({simulate_gpus} GPU{'s' if simulate_gpus != 1 else ''})"
        )
        method_bms, _ = _benchmark_simulated_gpu(simulate_gpus)
    else:
        gpu_backend = "none (no GPU available, use --simulate-gpus N)"
        method_bms = []

    projections = _compute_projections(method_bms) if method_bms else []

    call_breakdown = _collect_call_breakdown()

    return BenchmarkReport(
        timestamp=_now_iso(),
        mode="all",
        hostname=os.uname().nodename,
        gpu_backend=gpu_backend,
        gpu_count_real=real_count,
        simulated=simulated,
        call_breakdown=call_breakdown,
        method_benchmarks=method_bms,
        projections=projections,
    )


def print_report(report: BenchmarkReport) -> None:
    sep = "─" * 72

    print(f"\n{' GPU Monitoring Overhead Benchmark ':=^72}")
    print(f"  Host:        {report.hostname}")
    print(f"  GPU backend: {report.gpu_backend}")
    print(f"  Simulated:   {report.simulated}")
    print(f"  Timestamp:   {report.timestamp}")

    if report.simulated:
        print(f"\n{' ⚠ SIMULATED — No real GPU detected ':=^72}")
        print("  Call latencies are estimated (see SIMULATED_LATENCY_US in script).")
        print("  Run this on an NVIDIA GPU machine for real hardware measurements.")

    # NVML call breakdown
    print(f"\n{sep}")
    print(f"{' NVML Call Breakdown (per GPU, per call to get_gpu_details) ':=^72}")
    print(f"{'NVML Call':40s} {'Latency (µs)':15s} {'Used by monitor':20s}")
    print("-" * 72)
    for cb in report.call_breakdown:
        used = "YES" if cb["used_by_monitor"] else ""
        print(
            f"{cb['call_name']:40s} {cb['simulated_latency_us']:>10.0f} µs  {used:20s}"
        )

    unused = sum(1 for cb in report.call_breakdown if not cb["used_by_monitor"])
    total = len(report.call_breakdown)
    print(f"\n  → {unused}/{total} NVML calls DISCARDED by _monitor_power()")
    print(f"  → Only 1/{total} calls actually used (gpu_utilization)")

    # Method benchmarks
    if report.method_benchmarks:
        print(f"\n{sep}")
        print(f"{' Method Latency Benchmarks ':=^72}")
        print(
            f"{'Method':50s} {'p50':>8s} {'mean':>8s} {'p95':>8s}  {'NVML calls/s':>14s}"
        )
        print("-" * 72)
        for mb in report.method_benchmarks:
            lat = mb["latency_per_call_ms"]
            print(
                f"{mb['method']:50s} "
                f"{lat['p50_ms']:>7.2f}ms {lat['mean_ms']:>7.2f}ms {lat['p95_ms']:>7.2f}ms  "
                f"{mb['nvml_calls_per_second']:>8d}/s"
            )

    # Projections
    if report.projections:
        print(f"\n{sep}")
        print(f"{' Projected Savings (heavyweight → lightweight) ':=^72}")
        print(f"{'Metric':50s} {'Heavy':>12s} {'Light':>12s} {'Savings':>12s}")
        print("-" * 72)
        for p in report.projections:
            if "savings_pct" in p:
                print(
                    f"{p['metric']:50s} "
                    f"{p['heavy_path_ms']:>8.1f}ms {p['lightweight_path_ms']:>8.1f}ms "
                    f"{p['savings_ms']:>8.1f}ms ({p['savings_pct']}%)"
                )
            else:
                print(
                    f"{p['metric']:50s} "
                    f"{p['heavy_path_value']:>12,d} {p['lightweight_path_value']:>12,d} "
                    f"{p['savings_value']:>12,d}"
                )

    print(f"\n{sep}")
    print(f"{' Summary ':=^72}")
    if report.projections:
        hourly = next(
            (
                p
                for p in report.projections
                if p["metric"] == "Per-hour monitoring overhead"
            ),
            None,
        )
        daily = next(
            (
                p
                for p in report.projections
                if p["metric"] == "Per-day monitoring overhead (24h)"
            ),
            None,
        )
        nvml_daily = next(
            (p for p in report.projections if "NVML calls per hour" in p["metric"]),
            None,
        )
        if hourly:
            print(
                f"  Each second of monitoring saves   {hourly['savings_ms'] / 3600:.3f} ms"
            )
            print(
                f"  Per hour of continuous monitoring saves  {hourly['savings_ms'] / 1000:.1f} s"
            )
        if daily:
            print(
                f"  Per 24h day of monitoring saves   {daily['savings_ms'] / 1000:.0f} s ({daily['savings_ms'] / 60000:.1f} min)"
            )
        if nvml_daily:
            print(
                f"  Unnecessary NVML calls per 24h:    {nvml_daily['savings_value'] * 24:,d}"
            )
    print(f"{'=' * 72}\n")


def run_cold_subprocess(simulate_gpus: int | None = None) -> BenchmarkReport:
    """Spawn a fresh subprocess to measure cold-start GPU detection overhead."""
    cmd = [
        sys.executable,
        __file__,
        "cold",
        "--json",
    ]
    if simulate_gpus:
        cmd.extend(["--simulate-gpus", str(simulate_gpus)])
    env = os.environ.copy()
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if proc.returncode != 0:
        print(f"Subprocess failed: {proc.stderr[:500]}")
        return BenchmarkReport(
            timestamp=_now_iso(),
            mode="cold_subprocess",
            hostname=os.uname().nodename,
            gpu_backend="error",
            gpu_count_real=0,
            simulated=False,
            call_breakdown=[],
            method_benchmarks=[],
            projections=[],
            result="error",
        )
    report = json.loads(proc.stdout)
    report["mode"] = "cold_subprocess"
    report["result"] = f"cold_subprocess_overhead_ms={elapsed_ms:.1f}"
    return BenchmarkReport(**report)


def main() -> None:
    p = argparse.ArgumentParser(description="GPU monitoring overhead benchmark")
    p.add_argument("mode", nargs="?", default="quick", choices=["quick", "all", "cold"])
    p.add_argument(
        "--simulate-gpus",
        type=int,
        default=None,
        help="Simulate N GPUs (default: auto-detect)",
    )
    p.add_argument(
        "--json", action="store_true", help="Output JSON (for subprocess consumption)"
    )
    p.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS)
    args = p.parse_args()

    if args.mode == "quick":
        report = run_all(args.simulate_gpus)
        print_report(report)

    elif args.mode == "all":
        report = run_all(args.simulate_gpus)
        if args.json:
            print(json.dumps(asdict(report), default=str))
        else:
            print_report(report)

        # Also run cold subprocess if not already in one
        if not args.json and not os.environ.get("_BENCHMARK_CHILD"):
            print("\n--- Cold subprocess benchmark ---")
            cold_report = run_cold_subprocess(args.simulate_gpus)
            print(f"Cold subprocess overhead: {cold_report.result}")

    elif args.mode == "cold":
        os.environ["_BENCHMARK_CHILD"] = "1"
        report = run_all(args.simulate_gpus)
        if args.json:
            print(json.dumps(asdict(report), default=str))
        else:
            print_report(report)

    # Append to results file
    if not args.json and args.mode != "cold":
        with open(args.results_file, "a") as f:
            f.write(json.dumps(asdict(report), default=str) + "\n")
        print(f"→ Results appended to {args.results_file}")


if __name__ == "__main__":
    main()
