#!/usr/bin/env python3
"""Build ``global_energy_mix.json`` from the Our World in Data energy dataset.

The dataset combines the yearly electricity data of Ember and the Energy
Institute's Statistical Review of World Energy. To refresh the file, run:

    uv run python codecarbon/data/private_infra/update_global_energy_mix.py

The dataset is read from the Our World in Data catalog, or from a CSV file or
URL given as argument. Each country keeps its most recent year with an
electricity carbon intensity, stored in its ``year`` field. A carbon intensity
that is not positive is written as null. The sha256 of the dataset is printed, to record
which version was used.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import pandas as pd

OWID_ENERGY_URL = (
    "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv"
)

OUTPUT = Path(__file__).resolve().parent / "global_energy_mix.json"

# Dataset column -> key in global_energy_mix.json. Despite its key, per_capita_Wh is in kWh.
COLUMNS = {
    "country": "country_name",
    "iso_code": "iso_code",
    "year": "year",
    "electricity_carbon_intensity_gco2eq_per_kwh": "carbon_intensity",
    "fossil_fuels_electricity_twh": "fossil_TWh",
    "renewables_electricity_twh": "renewables_TWh",
    "electricity_generation_per_capita_kwh": "per_capita_Wh",
    "coal_electricity_twh": "coal_TWh",
    "gas_electricity_twh": "gas_TWh",
    "oil_electricity_twh": "oil_TWh",
    "solar_electricity_twh": "solar_TWh",
    "wind_electricity_twh": "wind_TWh",
    "hydro_electricity_twh": "hydroelectricity_TWh",
    "other_renewables_including_bioenergy_electricity_twh": "other_renewable_TWh",
    "other_renewables_excluding_bioenergy_electricity_twh": "other_renewable_exc_biofuel_TWh",
    "nuclear_electricity_twh": "nuclear_TWh",
    "bioenergy_electricity_twh": "biofuel_TWh",
    "low_carbon_electricity_twh": "low_carbon_TWh",
}


def read_dataset(source: str) -> Tuple[pd.DataFrame, str]:
    """Read the dataset from a file or URL, with the sha256 of its content."""
    if urlparse(source).scheme in ("http", "https"):
        with urllib.request.urlopen(source) as response:
            raw = response.read()
    else:
        raw = Path(source).read_bytes()
    return pd.read_csv(io.BytesIO(raw)), hashlib.sha256(raw).hexdigest()


def build_global_energy_mix(owid: pd.DataFrame) -> Dict[str, dict]:
    """Return the latest year of each country with a carbon intensity, by ISO code."""
    missing = sorted(set(COLUMNS) - set(owid.columns))
    if missing:
        raise ValueError(f"Columns missing from the dataset: {', '.join(missing)}")

    mix = owid[list(COLUMNS)].rename(columns=COLUMNS)
    mix = mix.dropna(subset=["carbon_intensity", "iso_code"])
    mix = mix.loc[mix.groupby("iso_code")["year"].idxmax()]
    mix["total_TWh"] = mix[["fossil_TWh", "renewables_TWh", "nuclear_TWh"]].sum(axis=1)
    mix = mix.fillna(0).round(3)
    mix["year"] = mix["year"].astype(int)
    records = mix.to_dict("records")
    for row in records:
        # A lifecycle carbon intensity cannot be zero, so such a value is written as
        # null and CodeCarbon computes the intensity from the mix instead.
        if row["carbon_intensity"] <= 0:
            row["carbon_intensity"] = None
    return {row["iso_code"]: row for row in records}


def check_global_energy_mix(
    mix: Dict[str, dict], previous: Dict[str, dict]
) -> List[str]:
    """Describe the entries to look at before trusting a refresh."""
    newest = max((row["year"] for row in mix.values()), default=0)
    problems = []
    for iso_code, row in sorted(mix.items()):
        if row["carbon_intensity"] is None:
            problems.append(
                f"{iso_code}: no positive carbon intensity, computed from the mix"
            )
        if row["total_TWh"] <= 0:
            problems.append(f"{iso_code}: no electricity generation in the mix")
        if row["year"] < newest - 2:
            problems.append(f"{iso_code}: latest data is from {row['year']}")
        if iso_code in previous and row["year"] < previous[iso_code]["year"]:
            problems.append(
                f"{iso_code}: year goes back from {previous[iso_code]['year']} to {row['year']}"
            )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "source",
        nargs="?",
        default=OWID_ENERGY_URL,
        help="dataset as a CSV file or URL, defaults to the Our World in Data catalog",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="defaults to global_energy_mix.json next to this script",
    )
    args = parser.parse_args()

    owid, sha256 = read_dataset(args.source)
    mix = build_global_energy_mix(owid)
    previous = {}
    if args.output.exists():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        lost = sorted(set(previous) - set(mix))
        if lost:
            raise SystemExit(f"Countries missing from the dataset: {', '.join(lost)}")
    args.output.write_text(
        json.dumps(mix, indent=4, sort_keys=True), encoding="utf-8", newline="\n"
    )

    years = Counter(row["year"] for row in mix.values())
    summary = ", ".join(f"{year}: {count}" for year, count in sorted(years.items()))
    print(f"Wrote {len(mix)} countries to {args.output} (years {summary})")
    print(f"Dataset sha256: {sha256}")
    for problem in check_global_energy_mix(mix, previous):
        print(f"Check: {problem}")


if __name__ == "__main__":
    main()
