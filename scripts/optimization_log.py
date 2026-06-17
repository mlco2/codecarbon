"""
Append high-level changes and benchmark speedups to .context/OPTIMIZATION_LOG.md.

Used by benchmark scripts after each run so optimization progress stays visible.
"""

from __future__ import annotations

import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / ".context" / "OPTIMIZATION_LOG.md"

# Baseline captured before optimization work began (2026-06-17, offline Mac).
BASELINE_MEASUREMENT = {
    "init_ms": 15667.8,
    "start_ms": 1008.7,
    "first_sample_ms": 18197.3,
    "cli_overhead_ms": 1519.6,
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _speedup(baseline: float, current: float) -> str:
    if baseline <= 0 or current <= 0:
        return "—"
    ratio = baseline / current
    pct = (1 - current / baseline) * 100
    return f"{ratio:.1f}× faster ({pct:.0f}% reduction)"


def _ensure_log_exists() -> None:
    if LOG_PATH.exists():
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(
        """# CodeCarbon Throughput Optimization Log

Living document tracking **code changes** and **measured speedups** for measurement launch and API throughput.

- JSONL raw data: `.context/measurement-benchmark-results.jsonl`, `.context/benchmark-results.jsonl`
- Re-run benchmarks: `uv run task benchmark-throughput`

## Current best — measurement launch (offline)

| Metric | Baseline | Current | Speedup |
|--------|----------|---------|---------|
| Tracker init | 15668 ms | — | — |
| start() | 1009 ms | — | — |
| First sample | 18197 ms | — | — |
| CLI monitor overhead | 1520 ms | — | — |

## Current best — API write path

| Metric | Baseline | Current | Speedup |
|--------|----------|---------|---------|
| POST /emissions p50 | — | — | — |
| Ponytail peak rps | — | — | — |

---

## Changelog

<!-- Newest entries at the top. -->

---

## Benchmark history

| Timestamp | Host | Mode | init_ms | start_ms | first_sample_ms | cli_overhead_ms | notes |
|-----------|------|------|---------|----------|-----------------|-----------------|-------|
"""
    )


def _update_current_best_table(
    content: str,
    section_header: str,
    rows: list[tuple[str, float, float]],
) -> str:
    """Update a markdown table section with baseline/current/speedup columns."""
    pattern = rf"(## {re.escape(section_header)}.*?)(\n---|\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content

    table_lines = [
        f"## {section_header}",
        "",
        "| Metric | Baseline | Current | Speedup |",
        "|--------|----------|---------|---------|",
    ]
    for metric, baseline, current in rows:
        table_lines.append(
            f"| {metric} | {baseline:.0f} ms | {current:.0f} ms | {_speedup(baseline, current)} |"
        )
    table_lines.append("")

    replacement = "\n".join(table_lines) + "\n"
    return content[: match.start()] + replacement + content[match.end(1) :]


def append_changelog_entry(
    title: str,
    changes: list[str],
    files: Optional[list[str]] = None,
) -> None:
    """Prepend a changelog entry (call after landing a code change)."""
    _ensure_log_exists()
    content = LOG_PATH.read_text()
    entry = [
        f"### {title} ({_now()})",
        "",
    ]
    for change in changes:
        entry.append(f"- {change}")
    if files:
        entry.append(f"- Files: `{', '.join(files)}`")
    entry.append("")
    content = content.replace(
        "## Changelog\n\n<!-- Newest entries at the top. -->\n\n",
        "## Changelog\n\n<!-- Newest entries at the top. -->\n\n"
        + "\n".join(entry)
        + "\n",
    )
    LOG_PATH.write_text(content)


def record_measurement_benchmark(results: dict[str, Any], mode: str = "startup") -> None:
    """Append a benchmark row and refresh the current-best table."""
    _ensure_log_exists()
    content = LOG_PATH.read_text()

    startup = results.get("startup") or {}
    cli = (results.get("cli_monitor") or {}) if isinstance(results.get("cli_monitor"), dict) else {}

    init_ms = startup.get("init_ms")
    start_ms = startup.get("start_ms")
    first_ms = startup.get("first_measurement_ms") or startup.get("launch_to_ready_ms")
    cli_ms = cli.get("cli_overhead_ms")

    host = socket.gethostname()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    row = (
        f"| {ts} | {host} | {mode} "
        f"| {init_ms or '—'} | {start_ms or '—'} | {first_ms or '—'} | {cli_ms or '—'} | auto |"
    )
    content = content.replace(
        "| Timestamp | Host | Mode | init_ms | start_ms | first_sample_ms | cli_overhead_ms | notes |\n"
        "|-----------|------|------|---------|----------|-----------------|-----------------|-------|\n",
        "| Timestamp | Host | Mode | init_ms | start_ms | first_sample_ms | cli_overhead_ms | notes |\n"
        "|-----------|------|------|---------|----------|-----------------|-----------------|-------|\n"
        f"{row}\n",
    )

    # Update current-best with latest non-null values vs baseline
    best_init = init_ms or BASELINE_MEASUREMENT["init_ms"]
    best_start = start_ms or BASELINE_MEASUREMENT["start_ms"]
    best_first = first_ms or BASELINE_MEASUREMENT["first_sample_ms"]
    best_cli = cli_ms or BASELINE_MEASUREMENT["cli_overhead_ms"]

    if init_ms:
        best_init = init_ms
    if start_ms:
        best_start = start_ms
    if first_ms:
        best_first = first_ms
    if cli_ms:
        best_cli = cli_ms

    # Read historical bests from table if present — use min values
    for line in content.splitlines():
        if line.startswith("| 20") and "auto" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 8:
                try:
                    if parts[3] != "—":
                        best_init = min(best_init, float(parts[3]))
                    if parts[4] != "—":
                        best_start = min(best_start, float(parts[4]))
                    if parts[5] != "—":
                        best_first = min(best_first, float(parts[5]))
                    if parts[6] != "—":
                        best_cli = min(best_cli, float(parts[6]))
                except ValueError:
                    pass

    content = _update_current_best_table(
        content,
        "Current best — measurement launch (offline)",
        [
            ("Tracker init", BASELINE_MEASUREMENT["init_ms"], best_init),
            ("start()", BASELINE_MEASUREMENT["start_ms"], best_start),
            ("First sample", BASELINE_MEASUREMENT["first_sample_ms"], best_first),
            ("CLI monitor overhead", BASELINE_MEASUREMENT["cli_overhead_ms"], best_cli),
        ],
    )

    LOG_PATH.write_text(content)


def record_api_benchmark(results: dict[str, Any]) -> None:
    """Record API ponytail results if present."""
    _ensure_log_exists()
    ponytail = results.get("ponytail") or {}
    if not ponytail:
        return
    steps = ponytail.get("steps") or []
    if not steps:
        return
    peak = ponytail.get("peak_throughput_step") or max(
        steps, key=lambda s: s.get("stats", {}).get("throughput_rps", 0)
    )
    stats = peak.get("stats", {})
    append_changelog_entry(
        f"API ponytail benchmark ({_now()})",
        [
            f"Peak throughput: {stats.get('throughput_rps', 0):.1f} rps "
            f"@ concurrency {peak.get('concurrency', '?')}",
            f"p50={stats.get('p50_ms', 0):.0f}ms p95={stats.get('p95_ms', 0):.0f}ms",
        ],
        files=["scripts/benchmark_codecarbon_api.py"],
    )


def record_profile_report(report: Any) -> None:
    """Append profiler hotspots to OPTIMIZATION_LOG.md."""
    _ensure_log_exists()
    content = LOG_PATH.read_text()

    lines = [
        f"### Profile — {report.timestamp} ({report.mode})",
        "",
        "| Phase | wall_ms | Top hotspot | cumul_ms |",
        "|-------|---------|-------------|----------|",
    ]
    all_recs: list[str] = []
    for phase in report.phases:
        top = phase.hotspots[0] if phase.hotspots else None
        if top:
            loc = f"`{top.file}:{top.line}` {top.function}"
            lines.append(
                f"| {phase.phase} | {phase.wall_ms} | {loc} | {top.cumulative_ms} |"
            )
        else:
            lines.append(f"| {phase.phase} | {phase.wall_ms} | — | — |")
        all_recs.extend(phase.recommendations)

    lines.append("")
    if all_recs:
        lines.append("**Profiler recommendations:**")
        seen: set[str] = set()
        for rec in all_recs:
            if rec not in seen:
                lines.append(f"- {rec}")
                seen.add(rec)
    lines.append("")

    marker = "## Profiler history\n\n<!-- Newest at top. -->\n\n"
    if marker not in content:
        content = content.replace(
            "## Next up (backlog)",
            "## Profiler history\n\n<!-- Newest at top. -->\n\n"
            + "## Next up (backlog)",
        )
    content = content.replace(marker, marker + "\n".join(lines) + "\n")

    # Refresh "latest hotspots" summary section
    summary_marker = "## Latest profiler hotspots\n\n"
    summary_lines = [summary_marker]
    for phase in report.phases[:5]:
        if not phase.hotspots:
            continue
        top = phase.hotspots[0]
        summary_lines.append(
            f"- **{phase.phase}** ({phase.wall_ms:.0f} ms wall): "
            f"`{top.file}:{top.line}` `{top.function}` — {top.cumulative_ms:.0f} ms cumulative"
        )
    summary_lines.append("")
    summary_block = "\n".join(summary_lines) + "\n"

    if summary_marker in content:
        import re as _re

        content = _re.sub(
            r"## Latest profiler hotspots\n\n.*?(?=\n---|\n## )",
            summary_block.rstrip() + "\n",
            content,
            count=1,
            flags=_re.DOTALL,
        )
    else:
        content = content.replace(
            "---\n\n## Changelog",
            "---\n\n" + summary_block + "---\n\n## Changelog",
        )

    LOG_PATH.write_text(content)
