#!/usr/bin/env python3
"""Fail when a numeric constant in the code no longer matches the docs.

Guards exactly one failure mode: a hardcoded number changes in
``codecarbon/`` while the page documenting it keeps the old value. Every
value is **imported from the codebase** (or loaded from the actual data
file) and then asserted to appear verbatim in the Markdown source. Nothing
here re-parses Python source with regexes -- a check that reads the code
textually can drift from the code it is supposed to guard.

Deliberately NOT in scope, do not extend it this way:

* **Prose accuracy.** Not mechanically checkable; a checker that tries
  produces noise.
* **Link checking.** ``scripts/check_docs_links.py`` already does it.
* **The order of any fallback ladder.** Verifying narrative structure
  false-fails, and a check that false-fails gets disabled -- which is worse
  than no check at all. If ladder ordering needs guarding, the honest tool
  is a unit test over ``codecarbon/core/resource_tracker.py``, not a docs
  check.

Two documented numbers are knowingly unguarded because they are inline
literals with no importable name: the ``0.1``/``0.9`` cpu_load cubic
coefficients (``external/hardware.py:287-288``) and the ``0.9/0.8/0.7`` RAM
marginal-efficiency multipliers (``external/ram.py:168-190``). Guarding them
would mean re-parsing source, which this script refuses to do. Give them
names in the code and they can be added here in one line each.

Usage: ``python scripts/check_docs_drift.py`` (exit 1 on drift).
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs" / "explanation"

sys.path.insert(0, str(REPO))

from codecarbon.core.cpu import DEFAULT_POWER_PER_CORE  # noqa: E402
from codecarbon.external.hardware import (  # noqa: E402
    CONSUMPTION_PERCENTAGE_CONSTANT,
    POWER_CONSTANT,
)
from codecarbon.external.ram import RAM_SLOT_POWER_X86  # noqa: E402


def _viz_data():
    """Import ``codecarbon.viz.data`` without requiring the dash extra.

    ``dash`` is only used there for a return annotation and a DataTable this
    script never calls, so a stub module is enough to reach the equivalence
    helpers.
    """
    if "dash" not in sys.modules:
        dash = types.ModuleType("dash")
        dash.dash_table = types.SimpleNamespace(DataTable=object)
        sys.modules["dash"] = dash
    from codecarbon.viz.data import Data

    # __init__ builds a DataSource we do not need; the helpers are pure.
    return Data.__new__(Data)


def _equivalence_divisors():
    """Recover the equivalence divisors by round-tripping the helpers.

    ``viz/data.py`` hardcodes these inline, so probe the functions instead of
    reading the source: if the divisor is ``d``, feeding ``d`` in must yield
    exactly one unit out.
    """
    data = _viz_data()
    return {
        "car, kg CO2e/mile": (
            0.409,
            lambda v: data.get_car_miles(v) == "1",
            "{} kg CO₂e per mile",
        ),
        "tv, kg CO2/hour": (
            0.097,
            lambda v: data.get_tv_time(v) == "60 minutes",
            "{} kg CO₂ per hour",
        ),
        "household, kg CO2/week": (
            160.58,
            lambda v: data.get_household_fraction(v) == "100.00",
            "{} kg CO₂ per week",
        ),
    }


def _checks(docs: Path = DOCS):
    """Yield (constant name, code value, string the docs must contain, page)."""
    methodology = docs / "methodology.md"
    equivalences = docs / "equivalences.md"

    intensity = json.loads(
        (
            REPO
            / "codecarbon"
            / "data"
            / "private_infra"
            / "carbon_intensity_per_source.json"
        ).read_text(encoding="utf-8")
    )
    world_average = intensity["world_average"]

    checks = [
        (
            "POWER_CONSTANT",
            POWER_CONSTANT,
            f"POWER_CONSTANT = {POWER_CONSTANT}",
            methodology,
        ),
        (
            "CONSUMPTION_PERCENTAGE_CONSTANT",
            CONSUMPTION_PERCENTAGE_CONSTANT,
            f"CONSUMPTION_PERCENTAGE_CONSTANT = {CONSUMPTION_PERCENTAGE_CONSTANT}",
            methodology,
        ),
        (
            "DEFAULT_POWER_PER_CORE",
            DEFAULT_POWER_PER_CORE,
            f"DEFAULT_POWER_PER_CORE = {DEFAULT_POWER_PER_CORE}",
            methodology,
        ),
        (
            "RAM_SLOT_POWER_X86",
            RAM_SLOT_POWER_X86,
            f"RAM_SLOT_POWER_X86 = {RAM_SLOT_POWER_X86}",
            methodology,
        ),
        (
            "RAM x86 power floor (2 x RAM_SLOT_POWER_X86)",
            RAM_SLOT_POWER_X86 * 2,
            f"{RAM_SLOT_POWER_X86 * 2} W (2 DIMMs × {RAM_SLOT_POWER_X86} W)",
            methodology,
        ),
        (
            "carbon_intensity_per_source.json: world_average",
            world_average,
            f"{world_average} gCO₂eq/kWh",
            methodology,
        ),
    ]

    for name, (value, round_trips, phrase) in _equivalence_divisors().items():
        if not round_trips(value):
            raise SystemExit(
                f"drift: the equivalence divisor for {name} in "
                f"codecarbon/viz/data.py is no longer {value}.\n"
                f"  fix: update this script's expected value and "
                f"{equivalences} to match the code."
            )
        checks.append(
            (f"equivalence, {name}", value, phrase.format(value), equivalences)
        )

    return checks


def _docs_say(text: str, needle: str) -> str:
    """Best-effort report of what the page says instead."""
    token = needle.split(" = ")[0] if " = " in needle else needle.split(" ")[0]
    hits = [
        line.strip()
        for line in text.splitlines()
        if token in line and token != line.strip()
    ]
    if not hits:
        return "the constant is not mentioned on the page at all"
    return "page says: " + " | ".join(hits[:3])


def main(docs: Path = DOCS) -> int:
    checks = _checks(docs)
    failures = []
    for name, value, needle, page in checks:
        text = page.read_text(encoding="utf-8")
        if needle not in text:
            failures.append(
                f"  {name}\n"
                f"    code value : {value}  (docs must contain {needle!r})\n"
                f"    docs       : {_docs_say(text, needle)}\n"
                f"    fix        : edit {page} to match the code -- or fix the "
                f"code if the docs are the correct value"
            )

    if failures:
        print(
            "Documentation drift: a constant changed in the code but the docs "
            "still show the old value.\n",
            file=sys.stderr,
        )
        print("\n\n".join(failures), file=sys.stderr)
        return 1

    print(f"docs drift check: {len(checks)} constants match the docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
