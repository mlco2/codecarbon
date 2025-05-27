from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest
from dash import dash_table as dt

from codecarbon.input import DataSource
from codecarbon.viz import data


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
