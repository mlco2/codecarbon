#!/usr/bin/env python3
"""
Benchmark repeated OfflineEmissionsTracker lifecycles per output method.

Measures init → start → stop throughput in one Python process (warm runs after
the first lifecycle). Network-backed outputs (API, HTTP) are mocked so results
reflect tracker + handler setup cost, not remote latency.

Usage:
    CODECARBON_ALLOW_MULTIPLE_RUNS=True uv run python scripts/benchmark_output_methods.py
    CODECARBON_ALLOW_MULTIPLE_RUNS=True uv run python scripts/benchmark_output_methods.py --runs 30 --json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codecarbon.core.hardware_cache import clear_cache as clear_hardware_cache
from codecarbon.core.output_cache import clear_cache as clear_output_cache
from codecarbon.core.config import clear_config_cache
from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.output_methods.base_output import OutputMethod


@dataclass
class LatencyStats:
    count: int
    min_ms: float
    max_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float


@dataclass
class ScenarioReport:
    label: str
    output_methods: list[str]
    runs: int
    cold_run_ms: float
    warm_run_ms: LatencyStats
    runs_per_minute: float


def compute_stats(values: list[float]) -> LatencyStats:
    if not values:
        return LatencyStats(0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ordered = sorted(values)
    n = len(ordered)

    def pct(p: float) -> float:
        idx = min(n - 1, max(0, int(p * n) - 1))
        return ordered[idx]

    return LatencyStats(
        count=n,
        min_ms=ordered[0],
        max_ms=ordered[-1],
        mean_ms=statistics.fmean(ordered),
        p50_ms=statistics.median(ordered),
        p95_ms=pct(0.95),
    )


@contextmanager
def _mocks_for_output_methods(methods: list[OutputMethod], tmp_dir: str):
    patches = []
    if OutputMethod.API in methods:
        mock_api = MagicMock()
        mock_api.run_id = None
        mock_api.experiment_id = "bench-exp"
        mock_api.add_emission.return_value = True
        patches.append(
            patch(
                "codecarbon.output_methods.http.get_or_create_api_client",
                return_value=mock_api,
            )
        )
    if OutputMethod.LOGFIRE in methods:
        mock_metrics = {name: MagicMock() for name in (
            "duration",
            "emissions",
            "energy_consumed",
            "emissions_rate",
            "cpu_power",
            "gpu_power",
            "ram_power",
            "cpu_energy",
            "gpu_energy",
            "ram_energy",
        )}
        patches.append(
            patch(
                "codecarbon.output_methods.metrics.logfire._ensure_logfire_metrics",
                return_value=mock_metrics,
            )
        )
    if OutputMethod.PROMETHEUS in methods:
        patches.append(
            patch(
                "codecarbon.output_methods.metrics.prometheus.push_to_gateway",
                return_value=None,
            )
        )
        patches.append(
            patch(
                "codecarbon.output_methods.metrics.prometheus.delete_from_gateway",
                return_value=None,
            )
        )

    started = [p.start() for p in patches]
    try:
        yield tmp_dir
    finally:
        for p in started:
            p.stop()


def _run_lifecycle(
    *,
    output_methods: list[OutputMethod],
    tmp_dir: str,
    measure_power_secs: float,
) -> float:
    t0 = time.perf_counter()
    with _mocks_for_output_methods(output_methods, tmp_dir):
        tracker = OfflineEmissionsTracker(
            country_iso_code="FRA",
            output_methods=output_methods or [],
            output_dir=tmp_dir,
            output_file="emissions.csv",
            measure_power_secs=measure_power_secs,
            log_level="error",
            save_to_file=False,
            save_to_api=False,
            api_call_interval=-1,
            api_endpoint="http://bench.test",
            api_key="bench-key",
            experiment_id="bench-exp",
            prometheus_url="http://bench.test:9091",
        )
        tracker.start()
        tracker.stop()
    return (time.perf_counter() - t0) * 1000


def benchmark_scenario(
    *,
    label: str,
    output_methods: list[OutputMethod],
    runs: int,
    measure_power_secs: float,
) -> ScenarioReport:
    clear_hardware_cache()
    clear_output_cache()
    clear_config_cache()

    with tempfile.TemporaryDirectory() as tmp_dir:
        durations_ms: list[float] = []
        for _ in range(runs):
            durations_ms.append(
                _run_lifecycle(
                    output_methods=output_methods,
                    tmp_dir=tmp_dir,
                    measure_power_secs=measure_power_secs,
                )
            )

    warm = durations_ms[1:] if len(durations_ms) > 1 else []
    total_s = sum(durations_ms) / 1000
    return ScenarioReport(
        label=label,
        output_methods=[m.value for m in output_methods],
        runs=runs,
        cold_run_ms=round(durations_ms[0], 2),
        warm_run_ms=compute_stats(warm),
        runs_per_minute=round(len(durations_ms) / total_s * 60, 1) if total_s else 0.0,
    )


SCENARIOS: list[tuple[str, list[OutputMethod]]] = [
    ("none", []),
    ("csv", [OutputMethod.CSV]),
    ("api", [OutputMethod.API]),
    ("logfire", [OutputMethod.LOGFIRE]),
    ("prometheus", [OutputMethod.PROMETHEUS]),
    ("logger", [OutputMethod.LOGGER]),
    ("csv+api", [OutputMethod.CSV, OutputMethod.API]),
    ("csv+logfire", [OutputMethod.CSV, OutputMethod.LOGFIRE]),
    ("all_live", [OutputMethod.CSV, OutputMethod.API, OutputMethod.LOGFIRE]),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--measure-power-secs", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("CODECARBON_ALLOW_MULTIPLE_RUNS", "True")

    reports: list[ScenarioReport] = []
    for label, methods in SCENARIOS:
        if methods == [OutputMethod.LOGGER]:
            continue  # requires user-supplied LoggerOutput instance
        report = benchmark_scenario(
            label=label,
            output_methods=methods,
            runs=args.runs,
            measure_power_secs=args.measure_power_secs,
        )
        reports.append(report)
        if not args.json:
            warm = report.warm_run_ms
            print(
                f"{label:12} cold={report.cold_run_ms:7.1f}ms  "
                f"warm_p50={warm.p50_ms:6.1f}ms  "
                f"warm_p95={warm.p95_ms:6.1f}ms  "
                f"runs/min={report.runs_per_minute:8.1f}"
            )

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": os.uname().nodename,
        "runs_per_scenario": args.runs,
        "scenarios": [asdict(r) for r in reports],
    }
    if args.json:
        print(json.dumps(payload, indent=2))

    out = REPO_ROOT / ".context" / "output-method-benchmark-results.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
