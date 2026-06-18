#!/usr/bin/env python3
"""
Micro-benchmark for retained perf optimizations (no handler singleton cache).

Compares:
  - config_load: cached get_hierarchical_config vs re-read each call
  - api_client: pooled get_or_create_api_client vs new ApiClient each call
  - logfire: configure-once vs clear_logfire_cache before each LogfireOutput
  - csv_flush: reused FileOutput (header cache warm) vs new FileOutput each append

Usage:
    uv run python scripts/benchmark_output_cache_micro.py
    uv run python scripts/benchmark_output_cache_micro.py --runs 50 --json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codecarbon.core.api_client import (  # noqa: E402
    ApiClient,
    clear_api_clients,
    get_or_create_api_client,
)
from codecarbon.core.config import (  # noqa: E402
    clear_config_cache,
    get_hierarchical_config,
)
from codecarbon.output_methods.emissions_data import EmissionsData  # noqa: E402
from codecarbon.output_methods.file import FileOutput  # noqa: E402
from codecarbon.output_methods.metrics.logfire import (  # noqa: E402
    LogfireOutput,
    clear_logfire_cache,
)


@dataclass
class BenchRow:
    section: str
    scenario: str
    mode: str
    cold_ms: float
    warm_p50_ms: float
    warm_p95_ms: float
    speedup: float | None


def p50(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(0.95 * len(ordered)) - 1))
    return ordered[idx]


def sample_emissions() -> EmissionsData:
    return EmissionsData(
        timestamp="2026-06-18T00:00:00",
        project_name="bench",
        run_id=str(uuid.uuid4()),
        experiment_id="bench-exp",
        duration=1.0,
        emissions=0.001,
        emissions_rate=0.001,
        cpu_power=10.0,
        gpu_power=0.0,
        ram_power=2.0,
        cpu_energy=0.01,
        gpu_energy=0.0,
        ram_energy=0.002,
        energy_consumed=0.012,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="",
        cloud_provider="",
        cloud_region="",
        os="bench",
        python_version="3.12",
        codecarbon_version="bench",
        cpu_count=8,
        cpu_model="bench-cpu",
        gpu_count=0,
        gpu_model="",
        longitude=0.0,
        latitude=0.0,
        ram_total_size=16.0,
        tracking_mode="machine",
    )


def bench_loop(
    fn: Callable[[], None],
    runs: int,
    *,
    clear_before_each: bool,
    clear_fn: Callable[[], None] | None = None,
) -> tuple[float, list[float]]:
    durations: list[float] = []
    for _ in range(runs):
        if clear_before_each and clear_fn:
            clear_fn()
        t0 = time.perf_counter()
        fn()
        durations.append((time.perf_counter() - t0) * 1000)
    return durations[0], durations[1:] if len(durations) > 1 else []


def add_speedup_row(
    rows: list[BenchRow],
    *,
    section: str,
    scenario: str,
    cached_p50: float,
    baseline_p50: float,
) -> None:
    if baseline_p50 <= 0:
        return
    rows.append(
        BenchRow(
            section=section,
            scenario=scenario,
            mode="speedup_optimized_vs_baseline",
            cold_ms=0.0,
            warm_p50_ms=cached_p50,
            warm_p95_ms=baseline_p50,
            speedup=round(baseline_p50 / max(cached_p50, 0.001), 2),
        )
    )


def bench_config_load(runs: int) -> list[BenchRow]:
    rows: list[BenchRow] = []
    for mode, clear_each in (("cached_warm", False), ("read_each_run", True)):
        cold, warm = bench_loop(
            get_hierarchical_config,
            runs,
            clear_before_each=clear_each,
            clear_fn=clear_config_cache if clear_each else None,
        )
        rows.append(
            BenchRow(
                section="config_load",
                scenario="get_hierarchical_config",
                mode=mode,
                cold_ms=round(cold, 3),
                warm_p50_ms=round(p50(warm), 3),
                warm_p95_ms=round(p95(warm), 3),
                speedup=None,
            )
        )
    add_speedup_row(
        rows,
        section="config_load",
        scenario="get_hierarchical_config",
        cached_p50=next(r.warm_p50_ms for r in rows if r.mode == "cached_warm"),
        baseline_p50=next(r.warm_p50_ms for r in rows if r.mode == "read_each_run"),
    )
    return rows


def bench_api_client(runs: int) -> list[BenchRow]:
    conf = {"cpu_model": "bench-cpu", "gpu_count": 0}
    rows: list[BenchRow] = []

    def pooled():
        get_or_create_api_client(
            endpoint_url="http://bench.test",
            experiment_id="bench-exp",
            api_key="bench-key",
            conf=conf,
        )

    def fresh():
        ApiClient(
            endpoint_url="http://bench.test",
            experiment_id="bench-exp",
            api_key="bench-key",
            conf=conf,
        )

    with patch("codecarbon.core.api_client.ApiClient._create_run"):
        for mode, clear_each, fn in (
            ("pooled_warm", False, pooled),
            ("new_client_each_run", True, fresh),
        ):
            cold, warm = bench_loop(
                fn,
                runs,
                clear_before_each=clear_each,
                clear_fn=clear_api_clients if clear_each else None,
            )
            rows.append(
                BenchRow(
                    section="api_client",
                    scenario="ApiClient construction",
                    mode=mode,
                    cold_ms=round(cold, 3),
                    warm_p50_ms=round(p50(warm), 3),
                    warm_p95_ms=round(p95(warm), 3),
                    speedup=None,
                )
            )

    add_speedup_row(
        rows,
        section="api_client",
        scenario="ApiClient construction",
        cached_p50=next(r.warm_p50_ms for r in rows if r.mode == "pooled_warm"),
        baseline_p50=next(
            r.warm_p50_ms for r in rows if r.mode == "new_client_each_run"
        ),
    )
    return rows


@contextmanager
def _logfire_mocks():
    mock_metrics = {
        name: MagicMock()
        for name in (
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
        )
    }
    with patch(
        "codecarbon.output_methods.metrics.logfire._ensure_logfire_metrics",
        return_value=mock_metrics,
    ):
        yield


def bench_logfire_init(runs: int) -> list[BenchRow]:
    rows: list[BenchRow] = []
    with _logfire_mocks():
        for mode, clear_each in (("configure_once", False), ("clear_each_run", True)):
            cold, warm = bench_loop(
                LogfireOutput,
                runs,
                clear_before_each=clear_each,
                clear_fn=clear_logfire_cache if clear_each else None,
            )
            rows.append(
                BenchRow(
                    section="logfire_init",
                    scenario="LogfireOutput()",
                    mode=mode,
                    cold_ms=round(cold, 3),
                    warm_p50_ms=round(p50(warm), 3),
                    warm_p95_ms=round(p95(warm), 3),
                    speedup=None,
                )
            )

    add_speedup_row(
        rows,
        section="logfire_init",
        scenario="LogfireOutput()",
        cached_p50=next(r.warm_p50_ms for r in rows if r.mode == "configure_once"),
        baseline_p50=next(r.warm_p50_ms for r in rows if r.mode == "clear_each_run"),
    )
    return rows


def bench_csv_flush(runs: int) -> list[BenchRow]:
    emissions = sample_emissions()
    delta = sample_emissions()
    rows: list[BenchRow] = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        seed = FileOutput("emissions.csv", tmp_dir, "append")
        seed.out(emissions, delta)

        reused = FileOutput("emissions.csv", tmp_dir, "append")
        for _ in range(3):
            reused.out(emissions, delta)

        for mode, use_reused in (
            ("reused_handler", True),
            ("new_handler_each_flush", False),
        ):
            durations: list[float] = []
            for _ in range(runs):
                t0 = time.perf_counter()
                if use_reused:
                    reused.out(emissions, delta)
                else:
                    FileOutput("emissions.csv", tmp_dir, "append").out(emissions, delta)
                durations.append((time.perf_counter() - t0) * 1000)
            rows.append(
                BenchRow(
                    section="csv_flush",
                    scenario="handler.out append",
                    mode=mode,
                    cold_ms=round(durations[0], 3),
                    warm_p50_ms=round(p50(durations[1:]), 3),
                    warm_p95_ms=round(p95(durations[1:]), 3),
                    speedup=None,
                )
            )

    add_speedup_row(
        rows,
        section="csv_flush",
        scenario="handler.out append",
        cached_p50=next(r.warm_p50_ms for r in rows if r.mode == "reused_handler"),
        baseline_p50=next(
            r.warm_p50_ms for r in rows if r.mode == "new_handler_each_flush"
        ),
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    all_rows: list[BenchRow] = []
    all_rows.extend(bench_config_load(args.runs))
    all_rows.extend(bench_api_client(args.runs))
    all_rows.extend(bench_logfire_init(args.runs))
    all_rows.extend(bench_csv_flush(args.runs))

    if not args.json:
        print("Retained optimization micro-benchmark\n")
        current_section = ""
        for row in all_rows:
            if row.section != current_section:
                current_section = row.section
                print(f"\n[{current_section}]")
            if row.mode.startswith("speedup"):
                print(
                    f"  {row.scenario:24} speedup: {row.speedup}x "
                    f"(optimized {row.warm_p50_ms:.3f}ms vs baseline {row.warm_p95_ms:.3f}ms)"
                )
            else:
                print(
                    f"  {row.scenario:24} {row.mode:24} "
                    f"cold={row.cold_ms:7.3f}ms warm_p50={row.warm_p50_ms:7.3f}ms"
                )

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": os.uname().nodename,
        "runs": args.runs,
        "rows": [asdict(r) for r in all_rows],
    }
    if args.json:
        print(json.dumps(payload, indent=2))

    out = REPO_ROOT / ".context" / "output-cache-micro-benchmark.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
