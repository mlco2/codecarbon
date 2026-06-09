import pandas as pd
import pytest

from codecarbon.viz import units


@pytest.mark.parametrize(
    ["data", "expected_unit"],
    [
        (pd.DataFrame({"emissions": [0.05, 0.564]}), units.EmissionUnit.GRAM),
        (pd.DataFrame({"emissions": [0.1, 2]}), units.EmissionUnit.KILOGRAM),
        (pd.DataFrame({"emissions": [2, 1001]}), units.EmissionUnit.KILOGRAM),
        (pd.DataFrame({"emissions": [1001, 2004]}), units.EmissionUnit.TON),
    ],
)
def test_get_emissions_unit(
    data: pd.DataFrame, expected_unit: units.EmissionUnit
) -> None:
    assert units.get_emissions_unit(data) == expected_unit


def test_extends_emissions_units() -> None:
    data = pd.DataFrame({"emissions": [0.5]})
    result = units.extends_emissions_units(data)
    assert result.equals(
        pd.DataFrame(
            {"emissions": [0.5], "emissions_in_g": [500.0], "emissions_in_t": [0.0005]}
        )
    )
