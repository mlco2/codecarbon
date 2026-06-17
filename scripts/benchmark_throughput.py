#!/usr/bin/env python3
"""
Unified throughput benchmark: measurement launch + API write path.

Runs measurement benchmarks first, then API benchmarks. Results append to
.context/throughput-benchmark-results.jsonl.

Usage:
    uv run python scripts/benchmark_throughput.py

    # Continuous regression
    uv run python scripts/benchmark_throughput.py --continuous --interval 120
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = REPO_ROOT / ".context" / "throughput-benchmark-results.jsonl"


@dataclass
class ThroughputReport:
    timestamp: str
    measurement: dict[str, Any] = field(default_factory=dict)
    api: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_script(script: str, args: list[str], timeout: float) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(REPO_ROOT)},
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_throughput_benchmark(args: argparse.Namespace) -> ThroughputReport:
    report = ThroughputReport(timestamp=_now_iso())
    print("=== Phase 1: Measurement launch & cycle overhead ===\n")

    code, out, err = _run_script(
        "benchmark_measurement.py",
        ["all", "--offline"] if args.offline else ["all"],
        timeout=args.measurement_timeout,
    )
    report.measurement["exit_code"] = code
    report.measurement["stdout"] = out[-4000:]
    if code != 0:
        report.errors.append(f"measurement benchmark failed: {err[-500:]}")
        print(err[-2000:])
    else:
        print(out[-2000:])

    print("\n=== Phase 2: API write-path throughput ===\n")
    api_args = ["ponytail", "--iterations", str(args.api_iterations)]
    if args.api_url:
        api_args.extend(["--api-url", args.api_url])
    if args.bootstrap:
        api_args.append("--bootstrap")

    code, out, err = _run_script(
        "benchmark_codecarbon_api.py",
        api_args,
        timeout=args.api_timeout,
    )
    report.api["exit_code"] = code
    report.api["stdout"] = out[-4000:]
    if code != 0:
        report.errors.append(f"API benchmark skipped or failed: {err[-500:]}")
        print(f"API benchmark note: {err[-500:] or 'no local API — set CODECARBON_API_URL + --bootstrap'}")
    else:
        print(out[-2000:])

    return report


def append_report(report: ThroughputReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(asdict(report), default=str) + "\n")
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from optimization_log import record_measurement_benchmark, record_api_benchmark

        if report.measurement.get("stdout"):
            import json as _json

            # Measurement results are printed, not structured — log points to JSONL
            pass
        record_api_benchmark({})
        print(f"→ see {REPO_ROOT / '.context' / 'OPTIMIZATION_LOG.md'}")
    except Exception:
        pass


def main() -> None:
    p = argparse.ArgumentParser(description="Unified CodeCarbon throughput benchmark")
    p.add_argument("--continuous", action="store_true")
    p.add_argument("--interval", type=float, default=120.0)
    p.add_argument("--offline", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--bootstrap", action="store_true", help="Bootstrap API test fixtures")
    p.add_argument("--api-url", default=None)
    p.add_argument("--measurement-timeout", type=float, default=300.0)
    p.add_argument("--api-timeout", type=float, default=300.0)
    p.add_argument("--api-iterations", type=int, default=10)
    p.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS)
    args = p.parse_args()

    if args.continuous:
        print(f"Continuous throughput benchmark every {args.interval}s")
        try:
            while True:
                report = run_throughput_benchmark(args)
                append_report(report, args.results_file)
                print(f"\n→ appended to {args.results_file}\n")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        report = run_throughput_benchmark(args)
        append_report(report, args.results_file)
        print(f"\n→ results appended to {args.results_file}")
        if report.errors:
            print("Warnings:", "; ".join(report.errors))


if __name__ == "__main__":
    main()
