"""
Generate a README badge from an existing ``emissions.csv``.

Everything here is local: read the CSV written by ``FileOutput`` and render a
`shields.io endpoint <https://shields.io/badges/endpoint-badge>`_ JSON file.
No network call, no hosted service, no account.
"""

import csv
import enum
import json
from pathlib import Path
from typing import Dict, List, Optional

BADGE_STEM = "codecarbon-badge"
LABEL = "carbon"
# The badge is deliberately colour-neutral. CodeCarbon numbers are often
# estimates, and a green badge on a large model would be greenwashing: no gram
# threshold is meaningful across arbitrary workloads.
COLOR = "#9f9f9f"


class Select(str, enum.Enum):
    last = "last"
    mean = "mean"
    total = "total"


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


def _timestamp(row: Dict) -> str:
    return row.get("timestamp") or ""


def last_row_per_run(rows: List[Dict]) -> List[Dict]:
    """
    Keep the latest row of each run, ordered by timestamp.

    CodeCarbon appends one row per flush, all sharing a ``run_id``, and every
    row holds the *cumulative* totals since the start of that run --
    ``FileOutput.out()`` discards the delta it is handed and writes the running
    total. Summing raw rows would therefore double-count.

    Rows are sorted by timestamp first: with ``allow_multiple_runs`` two
    trackers interleave their flushes into one file, so file order does not
    tell you which run finished last. Rows without a usable ``run_id`` (older
    CSVs, blank values) each count as their own run.
    """
    by_run: Dict[str, Dict] = {}
    for index, row in enumerate(sorted(rows, key=_timestamp)):
        by_run[row.get("run_id") or f"__norun{index}"] = row
    return sorted(by_run.values(), key=_timestamp)


def summarise(rows: List[Dict], select: Select = Select.last) -> Dict[str, float]:
    """
    Reduce the rows to the emissions and energy of a single reported value.
    """
    runs = last_row_per_run(rows)
    emissions = [float(row["emissions"]) for row in runs]
    energy = [float(row["energy_consumed"]) for row in runs]
    select = Select(select)
    if select is Select.last:
        value = {"emissions": emissions[-1], "energy_consumed": energy[-1]}
    elif select is Select.mean:
        value = {
            "emissions": sum(emissions) / len(emissions),
            "energy_consumed": sum(energy) / len(energy),
        }
    else:
        value = {"emissions": sum(emissions), "energy_consumed": sum(energy)}
    value["runs"] = len(runs)
    return value


def format_value(kilos: float, unit: str = "gCO2eq") -> str:
    """
    Format a value given in kg (or kWh) with a sensible scale, 3 significant
    digits. ``unit`` is the gram-scale (or Wh-scale) unit name.
    """
    scaled, prefix = kilos * 1000, ""
    magnitude = abs(scaled)
    if magnitude < 1:
        scaled, prefix = scaled * 1000, "m"
    elif magnitude >= 1_000_000:
        scaled, prefix = scaled / 1_000_000, "M"
    elif magnitude >= 1000:
        scaled, prefix = scaled / 1000, "k"
    return f"{scaled:.3g} {prefix}{unit}"


def message_for(summary: Dict[str, float], select: Select = Select.last) -> str:
    """
    Build the right-hand side of the badge from a summary.
    """
    suffix = {Select.last: "", Select.mean: "/run", Select.total: " total"}[
        Select(select)
    ]
    return format_value(summary["emissions"], "gCO2eq") + suffix


def render(summary: Dict[str, float], select: Select = Select.last) -> str:
    """
    Return the shields.io endpoint JSON of the badge for a summary.
    """
    return json.dumps(
        {
            "schemaVersion": 1,
            "label": LABEL,
            "message": message_for(summary, select),
            "color": COLOR,
        },
        indent=2,
    )


def write(
    summary: Dict[str, float], select: Select = Select.last, output_dir="."
) -> Path:
    """
    Write the badge JSON file and return its path.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{BADGE_STEM}.json"
    path.write_text(render(summary, select), encoding="utf-8")
    return path
