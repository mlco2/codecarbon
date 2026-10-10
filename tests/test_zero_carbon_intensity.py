from unittest.mock import patch

import pytest

from codecarbon.core.emissions import Emissions


@pytest.mark.parametrize("intensity", [0, 0.0, 42.0])
def test_explicit_carbon_intensity_is_used(intensity):
    with patch(
        "codecarbon.input.DataSource.get_carbon_intensity_per_source_data",
        side_effect=AssertionError("Source factors should not be needed"),
    ):
        rate = Emissions._global_energy_mix_to_emissions_rate(
            {"carbon_intensity": intensity}
        )
    assert rate.kgs_per_kWh == intensity / 1000


@pytest.mark.parametrize(
    "mix,expected",
    [
        ({"total_TWh": 1, "wind_TWh": 1}, 0.0),
        ({"total_TWh": 2, "wind_TWh": 1, "coal_TWh": 1}, 0.4),
        ({"total_TWh": 1, "coal_TWh": 1}, 0.8),
    ],
)
def test_zero_source_factor_counts_toward_energy_coverage(mix, expected):
    with patch(
        "codecarbon.input.DataSource.get_carbon_intensity_per_source_data",
        return_value={"wind": 0, "coal": 800, "world_average": 475},
    ):
        rate = Emissions._global_energy_mix_to_emissions_rate(mix)
    assert rate.kgs_per_kWh == expected
