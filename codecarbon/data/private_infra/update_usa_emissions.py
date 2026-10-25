#!/usr/bin/env python3
"""Build ``usa_emissions.json`` from the EPA eGRID data workbook.

Download the workbook from https://www.epa.gov/egrid/download-data, then run:

    uv run --with openpyxl python codecarbon/data/private_infra/update_usa_emissions.py \\
        egrid2023_data_rev2.xlsx --year 2023

The state rates come from the ``ST<yy>`` sheet and the national rate from the
``US<yy>`` sheet. Both sheets have a description row, then a row of eGRID
field names, then the data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

STATE_NAMES = {
    "AK": "alaska",
    "AL": "alabama",
    "AR": "arkansas",
    "AZ": "arizona",
    "CA": "california",
    "CO": "colorado",
    "CT": "connecticut",
    "DC": "district of columbia",
    "DE": "delaware",
    "FL": "florida",
    "GA": "georgia",
    "HI": "hawaii",
    "IA": "iowa",
    "ID": "idaho",
    "IL": "illinois",
    "IN": "indiana",
    "KS": "kansas",
    "KY": "kentucky",
    "LA": "louisiana",
    "MA": "massachusetts",
    "MD": "maryland",
    "ME": "maine",
    "MI": "michigan",
    "MN": "minnesota",
    "MO": "missouri",
    "MS": "mississippi",
    "MT": "montana",
    "NC": "north carolina",
    "ND": "north dakota",
    "NE": "nebraska",
    "NH": "new hampshire",
    "NJ": "new jersey",
    "NM": "new mexico",
    "NV": "nevada",
    "NY": "new york",
    "OH": "ohio",
    "OK": "oklahoma",
    "OR": "oregon",
    "PA": "pennsylvania",
    "RI": "rhode island",
    "SC": "south carolina",
    "SD": "south dakota",
    "TN": "tennessee",
    "TX": "texas",
    "UT": "utah",
    "VA": "virginia",
    "VT": "vermont",
    "WA": "washington",
    "WI": "wisconsin",
    "WV": "west virginia",
    "WY": "wyoming",
}

RATE_FIELDS = {
    "co2e": ("C2ERTA", "CO2 equivalent"),
    "co2": ("CO2RTA", "CO2"),
}


def read_egrid_rates(workbook: Path, year: int, gas: str = "co2e") -> tuple:
    """Return the state rates and the national rate (lb/MWh) for one gas."""
    yy = f"{year % 100:02d}"
    field = RATE_FIELDS[gas][0]
    states = pd.read_excel(workbook, sheet_name=f"ST{yy}", header=1)
    national = pd.read_excel(workbook, sheet_name=f"US{yy}", header=1)
    state_rates = dict(zip(states["PSTATABB"], states[f"ST{field}"]))
    return state_rates, float(national[f"US{field}"].iloc[0])


def build_usa_emissions(
    state_rates: dict, national_rate: float, year: int, gas: str = "co2e"
) -> dict:
    field, gas_label = RATE_FIELDS[gas]
    missing = sorted(set(STATE_NAMES) - set(state_rates))
    if missing:
        raise ValueError(f"States missing from eGRID{year}: {', '.join(missing)}")

    data = {
        "_unit": {
            "emissions": "lbs/MWh",
            "regionCode": "2 digit state/region code",
        },
        "_source": {
            "name": f"EPA eGRID{year}, annual {gas_label} total output emission rate",
            "url": "https://www.epa.gov/egrid/download-data",
            "field": f"ST{field}",
            "year": year,
        },
    }
    for code, name in sorted(STATE_NAMES.items(), key=lambda item: item[1]):
        data[name] = {
            "emissions": round(float(state_rates[code]), 3),
            "regionCode": code,
        }
    data["usa"] = {"emissions": round(national_rate, 3), "regionCode": "usa"}
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workbook", type=Path, help="eGRID data workbook (.xlsx)")
    parser.add_argument("--year", type=int, required=True, help="eGRID data year")
    parser.add_argument("--gas", choices=sorted(RATE_FIELDS), default="co2e")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="defaults to <year>/usa_emissions.json next to this script",
    )
    args = parser.parse_args()

    output = args.output or (
        Path(__file__).resolve().parent / str(args.year) / "usa_emissions.json"
    )
    state_rates, national_rate = read_egrid_rates(args.workbook, args.year, args.gas)
    data = build_usa_emissions(state_rates, national_rate, args.year, args.gas)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {len(STATE_NAMES)} states and the national rate to {output}")


if __name__ == "__main__":
    main()
