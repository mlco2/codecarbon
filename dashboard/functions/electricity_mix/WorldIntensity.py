# import os
# import sys
# currentdir = os.getcwd()
# currentdir = 'c:\\Users\\Client\\Desktop\\Projet CodeCarbon\\codecarbon'
# sys.path.append(os.path.abspath(currentdir))

import pandas as pd
from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata
from codecarbon.input import DataSource

DS = DataSource()
EM = Emissions(DS)
E = Energy(1)

df = pd.read_csv("dashboard/functions/electricity_mix/Country_ISO.csv", sep=";")

j = 0
df_intensity = pd.DataFrame(columns=["ISO", "Country", "CarbonIntensity"])
df_intensity["ISO"] = df["ISO"]
df_intensity["Country"] = df["Country"]

for i in df["ISO"]:
    GEO_i = GeoMetadata(i)
    df_intensity["CarbonIntensity"].iloc[j] = EM.get_country_emissions(E, GEO_i) * 1000
    j = j + 1

df_intensity.to_csv(
    "dashboard/functions/electricity_mix/WorldIntensity.csv", index=False
)
