"""
Generate a README badge from an existing ``emissions.csv``.

Everything here is local: read the CSV written by ``FileOutput`` and render a
`shields.io endpoint <https://shields.io/badges/endpoint-badge>`_ JSON file.
No network call, no hosted service, no account.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_LABEL = "carbon"
DEFAULT_COLOR = "#9f9f9f"
BADGE_STEM = "codecarbon-badge"

# The badge is deliberately colour-neutral by default. CodeCarbon numbers are
# often estimates, and a green badge on a large model would be greenwashing:
# no gram threshold is meaningful across arbitrary workloads.


def load_runs(emissions_file, project: Optional[str] = None) -> List[Dict]:
    """
    Read the rows of an emissions.csv, optionally keeping a single project.
    """
    path = Path(emissions_file)
    if not path.is_file():
        raise FileNotFoundError(f"No emissions file at {path}")
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if project is not None:
        rows = [row for row in rows if row.get("project_name") == project]
    if not rows:
        raise ValueError(
            f"No rows found in {path}"
            + (f" for project '{project}'" if project else "")
        )
    return rows


def last_row_per_run(rows: List[Dict]) -> List[Dict]:
    """
    Keep one row per run: the last one.

    CodeCarbon appends one row per flush, all sharing a ``run_id``, and every
    row holds the *cumulative* totals since the start of that run --
    ``FileOutput.out()`` discards the delta it is handed and writes the running
    total. Summing raw rows would therefore double-count. Files without a
    ``run_id`` column (older CSVs) are treated as one run per row.
    """
    if not rows or "run_id" not in rows[0]:
        return rows
    by_run: dict[str, dict] = {}
    for row in rows:
        by_run[row.get("run_id")] = row
    return list(by_run.values())


def summarise(rows: List[Dict], select: str = "last") -> Dict[str, float]:
    """
    Reduce the rows to the emissions and energy of a single reported value.
    """
    runs = last_row_per_run(rows)
    emissions = [float(row["emissions"]) for row in runs]
    energy = [float(row["energy_consumed"]) for row in runs]
    if select == "last":
        value = {"emissions": emissions[-1], "energy_consumed": energy[-1]}
    elif select == "mean":
        value = {
            "emissions": sum(emissions) / len(emissions),
            "energy_consumed": sum(energy) / len(energy),
        }
    elif select == "total":
        value = {"emissions": sum(emissions), "energy_consumed": sum(energy)}
    else:
        raise ValueError(f"Unknown selection '{select}', expected last/mean/total")
    value["runs"] = len(runs)
    return value


def format_value(kilos: float, unit: str = "gCO2eq") -> str:
    """
    Format a value given in kg (or kWh) with a sensible scale, 3 significant
    digits. ``unit`` is the gram-scale (or Wh-scale) unit name.
    """
    scaled, prefix = abs(kilos) * 1000, ""
    if scaled < 1:
        scaled, prefix = scaled * 1000, "m"
    elif scaled >= 1_000_000:
        scaled, prefix = scaled / 1_000_000, "M"
    elif scaled >= 1000:
        scaled, prefix = scaled / 1000, "k"
    return f"{scaled:.3g} {prefix}{unit}"


def render_endpoint_json(label: str, message: str, color: str = DEFAULT_COLOR) -> str:
    return json.dumps(
        {
            "schemaVersion": 1,
            "label": label,
            "message": message,
            "color": color,
        },
        indent=2,
    )


def render_markdown(label: str) -> str:
    return (
        f"![{label}](https://img.shields.io/endpoint"
        f"?url=<public-url-of>/{BADGE_STEM}.json)"
    )


def message_for(
    summary: Dict[str, float], select: str = "last", metric: str = "emissions"
) -> str:
    """
    Build the right-hand side of the badge from a summary.
    """
    suffix = {"last": "", "mean": "/run", "total": " total"}[select]
    parts = []
    if metric in ("emissions", "both"):
        parts.append(format_value(summary["emissions"], "gCO2eq"))
    if metric in ("energy", "both"):
        parts.append(format_value(summary["energy_consumed"], "Wh"))
    return " | ".join(parts) + suffix


def render(
    emissions_file="emissions.csv",
    project: Optional[str] = None,
    select: str = "last",
    metric: str = "emissions",
    label: str = DEFAULT_LABEL,
    color: str = DEFAULT_COLOR,
) -> str:
    """
    Return the shields.io endpoint JSON of the badge for an emissions file.
    """
    summary = summarise(load_runs(emissions_file, project), select)
    return render_endpoint_json(label, message_for(summary, select, metric), color)


def write(
    emissions_file="emissions.csv",
    project: Optional[str] = None,
    select: str = "last",
    metric: str = "emissions",
    label: str = DEFAULT_LABEL,
    color: str = DEFAULT_COLOR,
    output_dir=".",
) -> Path:
    """
    Write the badge JSON file and return its path.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{BADGE_STEM}.json"
    path.write_text(
        render(emissions_file, project, select, metric, label, color),
        encoding="utf-8",
    )
    return path
