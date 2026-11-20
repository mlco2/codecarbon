import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "codecarbon/data/private_infra/update_usa_emissions.py"
)
DATA = (
    Path(__file__).resolve().parents[1]
    / "codecarbon/data/private_infra/2023/usa_emissions.json"
)

# The script is a maintenance tool that is not shipped in the wheel, so the
# wheel test run (which only checks out tests/) does not have it.
pytestmark = pytest.mark.skipif(
    not SCRIPT.exists(), reason="update script is not part of the installed package"
)


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("update_usa_emissions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rates(script, value=500.0):
    return {code: value for code in script.STATE_NAMES}


def test_build_has_every_state_and_the_national_rate(script):
    data = script.build_usa_emissions(_rates(script), 600.0, 2023)

    assert data["georgia"] == {"emissions": 500.0, "regionCode": "GA"}
    assert data["district of columbia"]["regionCode"] == "DC"
    assert data["usa"] == {"emissions": 600.0, "regionCode": "usa"}
    assert data["_source"]["field"] == "STC2ERTA"
    assert len([k for k in data if not k.startswith("_")]) == 52


def test_build_can_use_co2_only_rates(script):
    data = script.build_usa_emissions(_rates(script), 600.0, 2023, gas="co2")

    assert data["_source"]["field"] == "STCO2RTA"


def test_build_rejects_a_missing_state(script):
    rates = _rates(script)
    del rates["WY"]

    with pytest.raises(ValueError, match="WY"):
        script.build_usa_emissions(rates, 600.0, 2023)


def test_extra_regions_are_ignored(script):
    rates = _rates(script)
    rates["PR"] = 1548.5

    data = script.build_usa_emissions(rates, 600.0, 2023)

    assert "puerto rico" not in data
    assert all(v.get("regionCode") != "PR" for v in data.values())


def test_packaged_file_matches_the_script_format(script):
    packaged = json.loads(DATA.read_text())
    state_rates = {
        v["regionCode"]: v["emissions"]
        for k, v in packaged.items()
        if not k.startswith("_") and k != "usa"
    }

    rebuilt = script.build_usa_emissions(
        state_rates, packaged["usa"]["emissions"], 2023
    )

    assert rebuilt == packaged


def test_read_egrid_rates_from_workbook(script, tmp_path):
    pytest.importorskip("openpyxl")
    import pandas as pd

    workbook = tmp_path / "egrid.xlsx"
    with pd.ExcelWriter(workbook) as writer:
        for sheet, frame in {
            "ST23": pd.DataFrame({"PSTATABB": ["GA", "VT"], "STC2ERTA": [717.4, 52.2]}),
            "US23": pd.DataFrame({"USC2ERTA": [770.9]}),
        }.items():
            pd.DataFrame([["description"] * len(frame.columns)]).to_excel(
                writer, sheet_name=sheet, index=False, header=False
            )
            frame.to_excel(writer, sheet_name=sheet, index=False, startrow=1)

    state_rates, national_rate = script.read_egrid_rates(workbook, 2023)

    assert state_rates == {"GA": 717.4, "VT": 52.2}
    assert national_rate == 770.9
