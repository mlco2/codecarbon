"""
Summarise an ``emissions.csv`` produced by CodeCarbon, optionally against a
baseline run, and render it for a CI job summary or a pull request comment.

Kept free of any CI-vendor specifics so GitLab, Jenkins, Buildkite and GitHub
Actions can all consume it.
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


class CIReportError(Exception):
    """Raised when an emissions CSV cannot be read or makes no sense."""


@dataclass
class RunSummary:
    """Totals for a single CodeCarbon run, aggregated from its CSV rows."""

    emissions: float
    energy_consumed: float
    duration: float
    rows: int
    project_name: str = ""
    country_iso_code: str = ""
    region: str = ""


def _to_float(value: Optional[str]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def summarise(csv_path: Path) -> RunSummary:
    """
    Aggregate the rows of the most recent run in ``csv_path``.

    During a run CodeCarbon appends one row per flush, each holding the delta
    since the previous one, all sharing the same ``run_id``. Summing the rows of
    the last ``run_id`` therefore gives the totals of that run, and degrades to
    the single row when the run was written only once.
    """
    if not csv_path.is_file():
        raise CIReportError(f"No emissions file found at {csv_path}")

    with open(csv_path, newline="") as csv_file:
        rows: List[Dict[str, str]] = list(csv.DictReader(csv_file))

    if not rows:
        raise CIReportError(f"No emissions data in {csv_path}")
    if "emissions" not in rows[0]:
        raise CIReportError(
            f"{csv_path} does not look like a CodeCarbon emissions file"
            " (no 'emissions' column)"
        )

    last_run_id = rows[-1].get("run_id")
    run_rows = [row for row in rows if row.get("run_id") == last_run_id]

    return RunSummary(
        emissions=sum(_to_float(row.get("emissions")) for row in run_rows),
        energy_consumed=sum(_to_float(row.get("energy_consumed")) for row in run_rows),
        duration=sum(_to_float(row.get("duration")) for row in run_rows),
        rows=len(run_rows),
        project_name=run_rows[-1].get("project_name") or "",
        country_iso_code=run_rows[-1].get("country_iso_code") or "",
        region=run_rows[-1].get("region") or "",
    )


def _format_delta(current: float, baseline: float) -> str:
    delta = current - baseline
    sign = "+" if delta >= 0 else "-"
    text = f"{sign}{abs(delta) * 1000:.1f} g"
    if baseline:
        text += f" ({sign}{abs(delta) / baseline * 100:.0f}%)"
    return text


def render_markdown(
    summary: RunSummary,
    baseline: Optional[RunSummary] = None,
    label: str = "",
) -> str:
    header = "**🌱 CodeCarbon**"
    if label:
        header += f" — `{label}`"
    elif summary.project_name:
        header += f" — `{summary.project_name}`"

    line = (
        f"**{summary.emissions * 1000:.1f} g CO2eq**"
        f" ({summary.energy_consumed:.3f} kWh, {summary.duration:.0f} s)"
    )
    if baseline is not None:
        line += (
            f" — **{_format_delta(summary.emissions, baseline.emissions)}** vs baseline"
        )

    location = summary.region or summary.country_iso_code
    footer = "Measured with CodeCarbon"
    if location:
        footer += f" in `{location}`"
    footer += (
        ". On virtualised CI runners CPU energy is estimated from the CPU model TDP,"
        " so values are comparable between runs on identical runners"
        " rather than absolute."
    )

    return f"{header}\n{line}\n\n_{footer}_"


def render_json(
    summary: RunSummary,
    baseline: Optional[RunSummary] = None,
    label: str = "",
) -> str:
    payload = {
        "label": label or summary.project_name,
        "emissions_kg": summary.emissions,
        "energy_kwh": summary.energy_consumed,
        "duration_seconds": summary.duration,
        "country_iso_code": summary.country_iso_code,
        "region": summary.region,
        "baseline_emissions_kg": None if baseline is None else baseline.emissions,
        "delta_kg": (
            None if baseline is None else summary.emissions - baseline.emissions
        ),
    }
    return json.dumps(payload, indent=2)


def render(
    summary: RunSummary,
    baseline: Optional[RunSummary] = None,
    label: str = "",
    output_format: str = "markdown",
) -> str:
    """Render a summary in the requested format."""
    if output_format == "markdown":
        return render_markdown(summary, baseline, label)
    if output_format == "json":
        return render_json(summary, baseline, label)
    raise CIReportError(
        f"Unknown format '{output_format}' (should be 'markdown' or 'json')"
    )
