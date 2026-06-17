#!/usr/bin/env python3
"""
Ponytail-scale profiler for CodeCarbon optimization.

Profiles launch/measurement in widening "tails" (init → start → first sample → cycles),
then ramps workload intensity — same ponytail scale as benchmarks.

Outputs:
  .context/profile-results.jsonl     — structured runs
  .context/profile-latest.txt        — human-readable top hotspots
  OPTIMIZATION_LOG.md                — updated via optimization_log.py

Usage:
    uv run python scripts/profile_optimization.py ponytail
    uv run python scripts/profile_optimization.py phase init
    uv run python scripts/profile_optimization.py iterate   # profile + benchmark + log
"""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_JSONL = REPO_ROOT / ".context" / "profile-results.jsonl"
PROFILE_LATEST = REPO_ROOT / ".context" / "profile-latest.txt"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


@dataclass
class Hotspot:
    function: str
    file: str
    line: int
    cumulative_ms: float
    per_call_ms: float
    calls: int


@dataclass
class ProfilePhaseResult:
    phase: str
    wall_ms: float
    hotspots: list[Hotspot] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ProfileReport:
    timestamp: str
    hostname: str
    mode: str
    phases: list[ProfilePhaseResult] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_offline_tracker():
    from codecarbon import OfflineEmissionsTracker

    return OfflineEmissionsTracker(
        measure_power_secs=1.0,
        output_methods=[],
        log_level="critical",
        allow_multiple_runs=True,
        tracking_mode="machine",
        country_iso_code="FRA",
    )


def _extract_hotspots(stats: pstats.Stats, limit: int = 15) -> list[Hotspot]:
    stats.calc_callees()
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    hotspots: list[Hotspot] = []
    for (file, line, func), (nc, _cc, _tt, ct, _callers) in stats.stats.items():
        if file.startswith("<") or "profile_optimization" in file:
            continue
        normalized = file.replace("\\", "/")
        if not normalized.startswith(str(REPO_ROOT).replace("\\", "/")):
            if "/codecarbon/" not in normalized and "/carbonserver/" not in normalized:
                continue
        per_call = (ct / nc * 1000) if nc else 0.0
        hotspots.append(
            Hotspot(
                function=func,
                file=file.replace(str(REPO_ROOT) + "/", "").replace(str(REPO_ROOT) + "\\", ""),
                line=line,
                cumulative_ms=round(ct * 1000, 2),
                per_call_ms=round(per_call, 2),
                calls=nc,
            )
        )
    hotspots.sort(key=lambda h: h.cumulative_ms, reverse=True)
    return hotspots[:limit]


def _recommendations(phase: str, hotspots: list[Hotspot]) -> list[str]:
    recs: list[str] = []
    for h in hotspots[:8]:
        path = h.file
        if phase in ("init", "ponytail_init") and "resource_tracker" in path:
            recs.append(f"Defer or parallelize hardware setup ({h.function}: {h.cumulative_ms:.0f}ms)")
        elif "powermetrics" in path or "powergadget" in path:
            recs.append(f"Cache or lazy-init power backend probe ({h.function}: {h.cumulative_ms:.0f}ms)")
        elif "geography" in path or "geo_js" in path:
            recs.append(f"Lazy geo lookup ({h.function}: {h.cumulative_ms:.0f}ms)")
        elif "api_client" in path:
            recs.append(f"Defer API run creation / use session pool ({h.function}: {h.cumulative_ms:.0f}ms)")
        elif "gpu" in path and h.cumulative_ms > 50:
            recs.append(f"Lazy GPU init ({h.function}: {h.cumulative_ms:.0f}ms)")
        elif "hardware.py" in path and "cpu_load" in h.function:
            recs.append(
                f"Use non-blocking psutil.cpu_percent after priming ({h.function}: {h.cumulative_ms:.0f}ms)"
            )
        elif "psutil" in path and "cpu_percent" in h.function:
            recs.append(
                f"Reduce cpu_percent blocking interval ({h.function}: {h.cumulative_ms:.0f}ms)"
            )
        elif "config" in path and h.cumulative_ms > 20:
            recs.append(f"Reduce config file I/O on hot path ({h.function}: {h.cumulative_ms:.0f}ms)")
    if not recs and hotspots:
        top = hotspots[0]
        recs.append(f"Investigate top hotspot: {top.file}:{top.line} {top.function} ({top.cumulative_ms:.0f}ms)")
    return recs[:5]


def profile_callable(phase: str, fn: Callable[[], None]) -> ProfilePhaseResult:
    profiler = cProfile.Profile()
    t0 = time.perf_counter()
    profiler.enable()
    fn()
    profiler.disable()
    wall_ms = (time.perf_counter() - t0) * 1000

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    hotspots = _extract_hotspots(stats)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(25)

    return ProfilePhaseResult(
        phase=phase,
        wall_ms=round(wall_ms, 1),
        hotspots=hotspots,
        recommendations=_recommendations(phase, hotspots),
    )


def phase_init() -> None:
    _make_offline_tracker()


def phase_start() -> None:
    tracker = _make_offline_tracker()
    tracker.start()
    tracker.stop()


def phase_first_sample() -> None:
    tracker = _make_offline_tracker()
    tracker.start()
    deadline = time.perf_counter() + 15
    while tracker._measure_occurrence < 1 and time.perf_counter() < deadline:
        time.sleep(0.02)
    tracker.stop()


def phase_cycles(n: int = 3) -> None:
    tracker = _make_offline_tracker()
    tracker.start()
    target = tracker._measure_occurrence + n
    deadline = time.perf_counter() + 30
    while tracker._measure_occurrence < target and time.perf_counter() < deadline:
        time.sleep(0.02)
    tracker.stop()


def phase_cli_monitor() -> None:
    import subprocess

    subprocess.run(
        [
            sys.executable,
            "-m",
            "codecarbon.cli.main",
            "monitor",
            "--log-level",
            "critical",
            "--measure-power-secs",
            "1",
            "--offline",
            "--country-iso-code",
            "FRA",
            "--",
            "-c",
            "import time; time.sleep(0.5)",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        timeout=60,
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(REPO_ROOT)},
        check=False,
    )


def phase_api_client_init() -> None:
    from codecarbon.core.api_client import ApiClient

    ApiClient(
        endpoint_url="https://api.codecarbon.io",
        experiment_id="5b0fa12a-3dd7-45bb-9766-cc326314d9f1",
        api_key="bench-key",
        conf={"os": "test", "python_version": "3.12", "codecarbon_version": "3.2.8"},
        create_run_automatically=False,
    )


def phase_api_boot() -> None:
    """Profile carbonserver FastAPI app import (API cold boot)."""
    import subprocess

    script = """
import os, sys, time
os.environ.setdefault("SKIP_DB_BOOTSTRAP", "1")
os.environ.setdefault("SKIP_DB_CREATE_ALL", "1")
t = time.perf_counter()
from main import app  # noqa: F401
print(round((time.perf_counter() - t) * 1000, 1))
"""
    subprocess.run(
        ["uv", "run", "--project", "carbonserver", "python", "-c", script],
        cwd=str(REPO_ROOT / "carbonserver"),
        env={**dict(**__import__("os").environ), "SKIP_DB_BOOTSTRAP": "1", "SKIP_DB_CREATE_ALL": "1"},
        check=False,
    )


PONYTAIL_PHASES: list[tuple[str, Callable[[], None]]] = [
    ("init", phase_init),
    ("start", phase_start),
    ("first_sample", phase_first_sample),
    ("cycles_3", lambda: phase_cycles(3)),
    ("cli_monitor", phase_cli_monitor),
]

API_PONYTAIL_PHASES: list[tuple[str, Callable[[], None]]] = [
    ("api_boot", phase_api_boot),
    ("api_client_init", phase_api_client_init),
]


def run_ponytail_profile(include_api: bool = False) -> ProfileReport:
    import socket

    phases: list[ProfilePhaseResult] = []
    print("Ponytail profiler — widening tails (init → start → sample → cycles)\n")
    for name, fn in PONYTAIL_PHASES:
        print(f"  profiling {name} ...")
        result = profile_callable(name, fn)
        phases.append(result)
        if result.hotspots:
            top = result.hotspots[0]
            print(
                f"    wall={result.wall_ms:.0f}ms  top={top.file}:{top.line} "
                f"{top.function} ({top.cumulative_ms:.0f}ms cumul)"
            )

    if include_api:
        print("  --- API tails ---")
        for name, fn in API_PONYTAIL_PHASES:
            print(f"  profiling {name} ...")
            result = profile_callable(name, fn)
            phases.append(result)
            if result.hotspots:
                top = result.hotspots[0]
                print(
                    f"    wall={result.wall_ms:.0f}ms  top={top.file}:{top.line} "
                    f"{top.function} ({top.cumulative_ms:.0f}ms cumul)"
                )

    return ProfileReport(
        timestamp=_now_iso(),
        hostname=socket.gethostname(),
        mode="ponytail",
        phases=phases,
    )


def run_single_phase(name: str) -> ProfileReport:
    import socket

    mapping = {n: fn for n, fn in PONYTAIL_PHASES}
    mapping.update({n: fn for n, fn in API_PONYTAIL_PHASES})
    if name not in mapping:
        raise SystemExit(f"Unknown phase: {name}. Choose from: {', '.join(mapping)}")
    result = profile_callable(name, mapping[name])
    return ProfileReport(
        timestamp=_now_iso(),
        hostname=socket.gethostname(),
        mode=f"phase:{name}",
        phases=[result],
    )


def save_report(report: ProfileReport) -> None:
    PROFILE_JSONL.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    with PROFILE_JSONL.open("a") as f:
        f.write(json.dumps(payload, default=str) + "\n")

    lines = [
        f"# Profile report — {report.timestamp}",
        f"Host: {report.hostname}  Mode: {report.mode}",
        "",
    ]
    for phase in report.phases:
        lines.append(f"## {phase.phase} (wall {phase.wall_ms} ms)")
        lines.append("")
        lines.append("| cumul_ms | per_call_ms | calls | location |")
        lines.append("|----------|-------------|-------|----------|")
        for h in phase.hotspots[:12]:
            loc = f"`{h.file}:{h.line}` `{h.function}`"
            lines.append(
                f"| {h.cumulative_ms} | {h.per_call_ms} | {h.calls} | {loc} |"
            )
        if phase.recommendations:
            lines.append("")
            lines.append("**Recommendations:**")
            for r in phase.recommendations:
                lines.append(f"- {r}")
        lines.append("")

    PROFILE_LATEST.write_text("\n".join(lines))

    try:
        from optimization_log import record_profile_report

        record_profile_report(report)
        print(f"\n→ updated {REPO_ROOT / '.context' / 'OPTIMIZATION_LOG.md'}")
    except Exception as exc:
        print(f"\n→ optimization log update skipped: {exc}")

    print(f"→ {PROFILE_LATEST}")
    print(f"→ appended {PROFILE_JSONL}")


def run_iterate(include_api: bool = False) -> None:
    """One optimization iteration: profile → benchmark → log."""
    print("=== Step 1/2: Ponytail profile ===\n")
    report = run_ponytail_profile(include_api=include_api)
    save_report(report)

    print("\n=== Step 2/2: Measurement benchmark ===\n")
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "benchmark_measurement.py"), "startup"],
        cwd=str(REPO_ROOT),
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(REPO_ROOT)},
    )
    if proc.returncode != 0:
        print("Benchmark failed — see output above")
        sys.exit(proc.returncode)

    print("\n=== Top recommendations this iteration ===")
    seen: set[str] = set()
    for phase in report.phases:
        for rec in phase.recommendations:
            if rec not in seen:
                print(f"  • {rec}")
                seen.add(rec)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ponytail-scale CodeCarbon profiler")
    p.add_argument(
        "mode",
        choices=["ponytail", "iterate", "phase"],
        help="ponytail=full ramp; iterate=profile+benchmark; phase=single phase",
    )
    p.add_argument("--phase", default="init", help="Phase name when mode=phase")
    p.add_argument("--include-api", action="store_true", help="Also profile ApiClient init")
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "ponytail":
        save_report(run_ponytail_profile(include_api=args.include_api))
    elif args.mode == "iterate":
        run_iterate(include_api=args.include_api)
    else:
        save_report(run_single_phase(args.phase))


if __name__ == "__main__":
    main()
