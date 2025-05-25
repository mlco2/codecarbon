from enum import Enum

import pandas as pd


class EmissionUnit(str, Enum):
    GRAM = "g"
    KILOGRAM = "kg"
    TON = "t"


def get_emissions_unit(data: pd.DataFrame) -> EmissionUnit:
    unit = EmissionUnit.KILOGRAM
    if (data.emissions < 1).all():
        unit = EmissionUnit.GRAM
    if (data.emissions > 1000).all():
        unit = EmissionUnit.TON
    return unit


def extends_emissions_units(data: pd.DataFrame) -> pd.DataFrame:
    data["emissions_in_g"] = data.emissions * 1000
    data["emissions_in_t"] = data.emissions / 1000
    return data
