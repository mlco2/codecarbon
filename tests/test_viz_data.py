from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest
from dash import dash_table as dt

from codecarbon.input import DataSource
from codecarbon.viz import data
from codecarbon.viz.components import Components


@pytest.fixture
def emissions_data() -> pd.DataFrame:
    tests_path = Path(__file__).parent
    return pd.read_csv(tests_path / "test_data/emissions_valid_headers.csv")


@pytest.fixture
def global_energy_mix_data() -> Dict[str, Dict[str, Any]]:
    return DataSource().get_global_energy_mix_data()


def test_get_project_data(emissions_data: pd.DataFrame):
    viz_data = data.Data()
    project_data = viz_data.get_project_data(emissions_data, project_name="codecarbon")
    assert isinstance(project_data, dt.DataTable)
    assert project_data.columns == [
        {"name": column, "id": column} for column in emissions_data.columns
    ]
    pd.testing.assert_frame_equal(pd.DataFrame(project_data.data), emissions_data)


def test_get_project_summary(emissions_data: pd.DataFrame):
    viz_data = data.Data()
    project_data = viz_data.get_project_data(emissions_data, project_name="codecarbon")
    project_summary = viz_data.get_project_summary(project_data.data)
    assert project_summary["last_run"]["timestamp"] == "2021-09-23T15:04:51"
    assert project_summary["total"]["duration"] == pytest.approx(161.20380687713623)
    assert project_summary["total"]["emissions"] == pytest.approx(0.0004490989249167)
    assert project_summary["total"]["energy_consumed"] == pytest.approx(
        0.00057442898176
    )
    assert project_summary["country_name"] == "Morocco"
    assert project_summary["country_iso_code"] == "MAR"
    assert project_summary["region"] == "casablanca-settat"
    assert project_summary["on_cloud"] == "N"


def test_get_project_summary_empty(emissions_data: pd.DataFrame):
    """Selecting no project used to raise an IndexError, see #918."""
    viz_data = data.Data()
    project_data = viz_data.get_project_data(emissions_data, project_name=None)
    assert project_data.data == []

    project_summary = viz_data.get_project_summary(project_data.data)
    assert project_summary == {
        "last_run": {
            "timestamp": "",
            "duration": 0,
            "emissions": 0,
            "energy_consumed": 0,
        },
        "total": {"duration": 0, "emissions": 0, "energy_consumed": 0},
        "country_name": "",
        "country_iso_code": "",
        "region": "",
        "on_cloud": "N",
        "cloud_provider": "",
        "cloud_region": "",
    }

    # The callbacks read the same keys whether or not a project is selected.
    populated_summary = viz_data.get_project_summary(
        viz_data.get_project_data(emissions_data, project_name="codecarbon").data
    )
    assert project_summary.keys() == populated_summary.keys()
    assert project_summary["last_run"].keys() == populated_summary["last_run"].keys()
    assert project_summary["total"].keys() == populated_summary["total"].keys()


def test_get_global_emissions_choropleth_data(
    global_energy_mix_data: Dict[str, Dict[str, Any]],
):
    viz_data = data.Data()
    choropleth_data = viz_data.get_global_emissions_choropleth_data(
        net_energy_consumed=100
    )
    assert sorted([row["iso_code"] for row in choropleth_data]) == sorted(
        global_energy_mix_data.keys()
    )
    expected_keys = [
        "iso_code",
        "emissions",
        "country",
        "carbon_intensity",
        "fossil",
        "hydroelectricity",
        "nuclear",
        "solar",
        "wind",
    ]
    assert all(list(row.keys()) == expected_keys for row in choropleth_data)


def test_get_country_choropleth_data():
    input_country_energy_mix = {
        "biofuel_TWh": 20.0,
        "carbon_intensity": 200,
        "coal_TWh": 50.0,
        "country_name": "Test",
        "fossil_TWh": 200.0,
        "gas_TWh": 120.0,
        "hydroelectricity_TWh": 200.0,
        "iso_code": "TST",
        "low_carbon_TWh": 110.0,
        "nuclear_TWh": 200.0,
        "oil_TWh": 30.0,
        "other_renewable_TWh": 25.0,
        "other_renewable_exc_biofuel_TWh": 5.0,
        "per_capita_TWh": 50.0,
        "renewables_TWh": 600.0,
        "solar_TWh": 275.0,
        "total_TWh": 1000.0,
        "wind_TWh": 100.0,
        "year": 2021,
    }
    expected_choropleth_data = {
        "iso_code": "TST",
        "emissions": 100,
        "carbon_intensity": 200,
        "country": "Test",
        "fossil": 20.0,
        "hydroelectricity": 20.0,
        "nuclear": 20.0,
        "solar": 27.5,
        "wind": 10.0,
    }
    viz_data = data.Data()
    output_choropleth_data = viz_data.get_country_choropleth_data(
        country_energy_mix=input_country_energy_mix,
        country_name="Test",
        country_iso_code="TST",
        country_emissions=100,
    )
    assert output_choropleth_data == expected_choropleth_data


def test_get_project_summary_skips_runs_without_measurement(
    emissions_data: pd.DataFrame,
):
    """A run with empty emissions and energy must not turn the totals into NaN."""
    unmeasured_run = emissions_data.iloc[[0]].assign(
        timestamp="2021-09-23T15:00:00",
        emissions=float("nan"),
        energy_consumed=float("nan"),
    )
    with_gap = pd.concat([unmeasured_run, emissions_data], ignore_index=True)
    viz_data = data.Data()
    project_data = viz_data.get_project_data(with_gap, project_name="codecarbon")

    project_summary = viz_data.get_project_summary(project_data.data)

    assert project_summary["total"]["emissions"] == pytest.approx(0.0004490989249167)
    assert project_summary["total"]["energy_consumed"] == pytest.approx(
        0.00057442898176
    )


def test_project_emissions_bar_chart_with_unmeasured_run():
    """A run with empty emissions must not break the bar chart."""
    project_data = pd.DataFrame(
        {
            "timestamp": ["2024-05-31T10:45:50", "2024-05-31T10:46:01"],
            "project_name": ["codecarbon", "codecarbon"],
            "emissions": [float("nan"), 0.0004],
            "energy_consumed": [float("nan"), 0.0005],
        }
    ).to_dict("records")

    figure = Components.get_project_emissions_bar_chart_figure(project_data)

    bars = figure.data[0]
    assert figure.layout.yaxis.title.text == "Carbon Equivalent (gCO2eq)"
    assert bars.orientation == "v"
    assert pd.isna(bars.y[0])
    assert bars.y[1] == 0.4


def test_get_regional_emissions_choropleth_data_skips_metadata_keys():
    viz_data = data.Data()

    choropleth_data = viz_data.get_regional_emissions_choropleth_data(
        net_energy_consumed=1.0, country_iso_code="USA"
    )

    usa_emissions = DataSource().get_country_emissions_data("usa")
    regions = [name for name in usa_emissions if not name.startswith("_")]
    assert [row["region_name"] for row in choropleth_data] == [
        name.upper() for name in regions
    ]
    assert all(row["emissions"] > 0 for row in choropleth_data)


def test_canada_regional_emissions_map_has_every_province():
    from codecarbon.viz.components import Components

    viz_data = data.Data()
    choropleth_data = viz_data.get_regional_emissions_choropleth_data(
        net_energy_consumed=1.0, country_iso_code="CAN"
    )

    figure = Components().get_regional_emissions_choropleth_figure(
        choropleth_data, "CAN"
    )

    assert sorted(row["region_code"] for row in choropleth_data) == sorted(
        ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE"]
        + ["QC", "SK", "YT"]
    )
    assert sorted(figure.data[0].locations) == list(range(1, 14))
    ontario = next(row for row in choropleth_data if row["region_code"] == "ON")
    assert ontario["emissions"] == pytest.approx(0.073, rel=1e-5)
