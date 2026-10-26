import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "codecarbon/data/private_infra/update_global_energy_mix.py"
)
DATA = (
    Path(__file__).resolve().parents[1]
    / "codecarbon/data/private_infra/global_energy_mix.json"
)

# The script is a maintenance tool that is not shipped in the wheel, so the
# wheel test run (which only checks out tests/) does not have it.
pytestmark = pytest.mark.skipif(
    not SCRIPT.exists(), reason="update script is not part of the installed package"
)


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("update_global_energy_mix", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _dataset(script, *rows):
    """A dataset with every expected column, zero where a row has no value."""
    frame = pd.DataFrame(rows)
    for column in script.COLUMNS:
        if column not in frame:
            frame[column] = 0.0
    return frame


def _france(year, intensity, **values):
    return {
        "country": "France",
        "iso_code": "FRA",
        "year": year,
        "electricity_carbon_intensity_gco2eq_per_kwh": intensity,
        **values,
    }


def test_keeps_the_latest_year_with_a_carbon_intensity(script):
    owid = _dataset(
        script, _france(2023, 56.0), _france(2024, 41.0), _france(2025, float("nan"))
    )

    mix = script.build_global_energy_mix(owid)

    assert mix["FRA"]["year"] == 2024
    assert mix["FRA"]["carbon_intensity"] == 41.0


def test_a_country_without_any_carbon_intensity_is_left_out(script):
    germany = {**_france(2024, 330.0), "country": "Germany", "iso_code": "DEU"}
    owid = _dataset(script, _france(2023, float("nan")), germany)

    mix = script.build_global_energy_mix(owid)

    assert list(mix) == ["DEU"]


def test_countries_are_keyed_by_iso_code_and_aggregates_are_ignored(script):
    world = {**_france(2024, 450.0), "country": "World", "iso_code": float("nan")}
    owid = _dataset(script, _france(2024, 41.0), world)

    mix = script.build_global_energy_mix(owid)

    assert list(mix) == ["FRA"]
    assert mix["FRA"]["country_name"] == "France"
    assert mix["FRA"]["iso_code"] == "FRA"


def test_missing_sources_are_zero_and_the_total_is_their_sum(script):
    owid = _dataset(
        script,
        _france(
            2024,
            41.0,
            fossil_fuels_electricity_twh=29.35,
            renewables_electricity_twh=148.56,
            nuclear_electricity_twh=392.07,
            solar_electricity_twh=float("nan"),
        ),
    )

    mix = script.build_global_energy_mix(owid)

    assert mix["FRA"]["solar_TWh"] == 0.0
    assert mix["FRA"]["total_TWh"] == 569.98


def test_values_are_rounded_to_three_decimals_and_the_year_is_an_integer(script):
    owid = _dataset(
        script,
        _france(2024.0, 41.4449, electricity_generation_per_capita_kwh=8551.734251),
    )

    mix = script.build_global_energy_mix(owid)

    assert mix["FRA"]["per_capita_Wh"] == 8551.734
    assert mix["FRA"]["carbon_intensity"] == 41.445
    assert isinstance(mix["FRA"]["year"], int)


def test_a_carbon_intensity_of_zero_is_written_as_null(script):
    caf = {
        "country": "Central African Republic",
        "iso_code": "CAF",
        "year": 2023,
        "electricity_carbon_intensity_gco2eq_per_kwh": 0.0,
        "hydro_electricity_twh": 0.14,
    }
    owid = _dataset(script, {**caf, "year": 2022}, caf)

    mix = script.build_global_energy_mix(owid)

    assert mix["CAF"]["year"] == 2023
    assert mix["CAF"]["carbon_intensity"] is None
    assert '"carbon_intensity": null' in json.dumps(mix)


def test_a_dataset_without_the_expected_columns_is_rejected(script):
    owid = _dataset(script, _france(2024, 41.0)).drop(columns=["coal_electricity_twh"])

    with pytest.raises(ValueError, match="coal_electricity_twh"):
        script.build_global_energy_mix(owid)


def _entry(year=2025, carbon_intensity=100.0, total_TWh=10.0):
    return {
        "year": year,
        "carbon_intensity": carbon_intensity,
        "total_TWh": total_TWh,
    }


def test_a_sound_refresh_has_nothing_to_check(script):
    mix = {"FRA": _entry(), "DEU": _entry(2023)}

    assert script.check_global_energy_mix(mix, {"FRA": _entry(2024)}) == []


def test_a_missing_carbon_intensity_is_flagged(script):
    mix = {"CAF": _entry(carbon_intensity=None), "FRA": _entry()}

    assert script.check_global_energy_mix(mix, {}) == [
        "CAF: no positive carbon intensity, computed from the mix"
    ]


def test_an_empty_mix_is_flagged(script):
    mix = {"XYZ": _entry(total_TWh=0.0), "FRA": _entry()}

    assert script.check_global_energy_mix(mix, {}) == [
        "XYZ: no electricity generation in the mix"
    ]


def test_countries_with_old_data_are_flagged(script):
    mix = {
        "ESH": _entry(2009),
        "LSO": _entry(2022),
        "FRA": _entry(),
        "DEU": _entry(2023),
    }

    assert script.check_global_energy_mix(mix, {}) == [
        "ESH: latest data is from 2009",
        "LSO: latest data is from 2022",
    ]


def test_a_year_going_backwards_is_flagged(script):
    mix = {"FRA": _entry(2024), "DEU": _entry(2025)}
    previous = {"FRA": _entry(2025), "DEU": _entry(2025)}

    assert script.check_global_energy_mix(mix, previous) == [
        "FRA: year goes back from 2025 to 2024"
    ]


def test_read_dataset_returns_the_hash_of_a_file(script, tmp_path):
    source = tmp_path / "owid_energy.csv"
    _dataset(script, _france(2024, 41.0)).to_csv(source, index=False)

    owid, sha256 = script.read_dataset(str(source))

    assert list(owid["iso_code"]) == ["FRA"]
    assert sha256 == hashlib.sha256(source.read_bytes()).hexdigest()


def test_read_dataset_downloads_a_url(script, monkeypatch):
    content = b"country,year\nFrance,2024\n"
    requested = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def read(self):
            return content

    def urlopen(url):
        requested.append(url)
        return Response()

    monkeypatch.setattr(script.urllib.request, "urlopen", urlopen)

    owid, sha256 = script.read_dataset("https://example.org/owid_energy.csv")

    assert requested == ["https://example.org/owid_energy.csv"]
    assert list(owid["country"]) == ["France"]
    assert sha256 == hashlib.sha256(content).hexdigest()


def test_packaged_file_matches_the_script_format(script):
    text = DATA.read_text(encoding="utf-8")
    packaged = json.loads(text)
    columns = {key: column for column, key in script.COLUMNS.items()}
    # null stands for a carbon intensity of zero in the dataset
    owid = pd.DataFrame(
        [
            {
                column: 0.0 if record[key] is None else record[key]
                for key, column in columns.items()
            }
            for record in packaged.values()
        ]
    )

    assert script.build_global_energy_mix(owid) == packaged
    assert json.dumps(packaged, indent=4, sort_keys=True) == text


def test_packaged_file_has_a_positive_total_for_every_country():
    # codecarbon.viz divides by total_TWh to show the share of each source
    packaged = json.loads(DATA.read_text(encoding="utf-8"))

    assert [iso for iso, row in packaged.items() if row["total_TWh"] <= 0] == []


def test_packaged_file_has_no_carbon_intensity_of_zero():
    # an explicit zero is used as is, which would report no emissions at all
    packaged = json.loads(DATA.read_text(encoding="utf-8"))
    intensities = [row["carbon_intensity"] for row in packaged.values()]

    assert [value for value in intensities if value is not None and value <= 0] == []


def _run(script, monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["update_global_energy_mix.py", *map(str, args)])
    script.main()


def test_main_writes_the_file(script, monkeypatch, tmp_path, capsys):
    source = tmp_path / "owid_energy.csv"
    _dataset(script, _france(2024, 41.0)).to_csv(source, index=False)
    output = tmp_path / "global_energy_mix.json"

    _run(script, monkeypatch, source, "--output", output)

    assert json.loads(output.read_text(encoding="utf-8"))["FRA"]["year"] == 2024
    printed = capsys.readouterr().out
    assert "Wrote 1 countries" in printed
    assert (
        f"Dataset sha256: {hashlib.sha256(source.read_bytes()).hexdigest()}" in printed
    )


def test_main_prints_what_to_check(script, monkeypatch, tmp_path, capsys):
    source = tmp_path / "owid_energy.csv"
    _dataset(script, _france(2024, 0.0)).to_csv(source, index=False)
    output = tmp_path / "global_energy_mix.json"

    _run(script, monkeypatch, source, "--output", output)

    assert (
        json.loads(output.read_text(encoding="utf-8"))["FRA"]["carbon_intensity"]
        is None
    )
    assert (
        "Check: FRA: no positive carbon intensity, computed from the mix"
        in capsys.readouterr().out
    )


def test_main_refuses_to_drop_a_country(script, monkeypatch, tmp_path):
    source = tmp_path / "owid_energy.csv"
    _dataset(script, _france(2024, 41.0)).to_csv(source, index=False)
    output = tmp_path / "global_energy_mix.json"
    output.write_text(json.dumps({"FRA": {}, "DEU": {}}), encoding="utf-8")

    with pytest.raises(SystemExit, match="DEU"):
        _run(script, monkeypatch, source, "--output", output)

    assert json.loads(output.read_text(encoding="utf-8")) == {"FRA": {}, "DEU": {}}
