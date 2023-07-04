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
    global_energy_mix_data: Dict[str, Dict[str, Any]]
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
        "fossil",
        "hydroelectricity",
        "nuclear",
        "solar",
        "wind",
    ]
    assert all(list(row.keys()) == expected_keys for row in choropleth_data)
