"""
Generate a README badge from an existing ``emissions.csv``.

Everything here is local: read the CSV written by ``FileOutput``, render a flat
SVG badge and a `shields.io endpoint
<https://shields.io/badges/endpoint-badge>`_ JSON file. No network call, no
hosted service, no account.
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

_SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {message}">
  <title>{label}: {message}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{message_width}" height="20" fill="{color}"/>
    <rect width="{width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_x}" y="14">{label}</text>
    <text x="{message_x}" y="15" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{message_x}" y="14">{message}</text>
  </g>
</svg>
"""


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


def summarise(rows: List[Dict], select: str = "last") -> Dict[str, float]:
    """
    Reduce the rows to the emissions and energy of a single reported value.
    """
    emissions = [float(row["emissions"]) for row in rows]
    energy = [float(row["energy_consumed"]) for row in rows]
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
    value["runs"] = len(rows)
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


def _text_width(text: str) -> int:
    # ponytail: character count times an average advance; real font metrics
    # would need a font dependency and would move the badge by a pixel or two.
    return int(len(text) * 6.5) + 20


def render_svg(label: str, message: str, color: str = DEFAULT_COLOR) -> str:
    label_width = _text_width(label)
    message_width = _text_width(message)
    return _SVG_TEMPLATE.format(
        label=_escape(label),
        message=_escape(message),
        color=color,
        width=label_width + message_width,
        label_width=label_width,
        message_width=message_width,
        label_x=label_width // 2,
        message_x=label_width + message_width // 2,
    )


def _escape(text: str) -> str:
    for char, entity in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
        text = text.replace(char, entity)
    return text


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


def render_markdown(label: str, output_dir=".") -> str:
    return (
        f"![{label}]({Path(output_dir) / (BADGE_STEM + '.svg')})\n"
        "\n"
        "or, publishing the endpoint JSON at a public URL:\n"
        "\n"
        f"![{label}](https://img.shields.io/endpoint?url=<your-url>/{BADGE_STEM}.json)"
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
    Return the SVG source of the badge for an emissions file.
    """
    summary = summarise(load_runs(emissions_file, project), select)
    return render_svg(label, message_for(summary, select, metric), color)


def write(
    emissions_file="emissions.csv",
    project: Optional[str] = None,
    select: str = "last",
    metric: str = "emissions",
    label: str = DEFAULT_LABEL,
    color: str = DEFAULT_COLOR,
    output_dir=".",
    formats=("svg", "json"),
) -> List[Path]:
    """
    Write the badge files and return the paths written.
    """
    summary = summarise(load_runs(emissions_file, project), select)
    message = message_for(summary, select, metric)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    if "svg" in formats:
        path = directory / f"{BADGE_STEM}.svg"
        path.write_text(render_svg(label, message, color), encoding="utf-8")
        written.append(path)
    if "json" in formats:
        path = directory / f"{BADGE_STEM}.json"
        path.write_text(render_endpoint_json(label, message, color), encoding="utf-8")
        written.append(path)
    return written
