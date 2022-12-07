import pandas as pd

# Lire le World Energy Mix (last version)
df1 = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/master/codecarbon/data/private_infra/world_energy_mix.csv",
).rename(columns={"country_name": "Country"})

# Lire les codes pays associés aux intensités carbone (2020)
df2 = pd.read_csv("dashboard/functions/electricity_mix/WorldIntensity.csv").rename(
    columns={"CarbonIntensity": "Carbon intensity of electricity (gCO2/kWh)"},
)
df2.iloc[:, 2] = round(df2.iloc[:, 2], 0)

# Agregation des intensités carbone et des mixs électrique
df = pd.merge(df2, df1, on=["Country"], how="outer")

df = df.drop(["Unnamed: 0", "country_id"], axis=1)
df["Total electricity generation"] = (
    df["Fossil fuels electricity generation"]
    + df["Geothermal electricity generation"]
    + df["Hydroelectricity generation"]
    + df["Nuclear power generation"]
    + df["Solar electricity generation"]
    + df["Wind electricity generation"]
)

# Sélection des codes ISO sans aucunes données (intensité = moyenne mondiale)
default_ISO = df[df["Year"].isna()].iloc[:, :4]
default_ISO = default_ISO.fillna("/")

# Sélection des dernières données disponibles pour les autres pays (last measure)

df = df.dropna(how="any")
measure = (
    df.groupby("ISO", as_index=False)
    .agg({"Year": "max"})
    .rename(columns={"Year": "Last Year"})
)

select = pd.merge(df, measure, on=["ISO"], how="inner")
select = select[select["Year"] == select["Last Year"]].drop(
    "Last Year",
    axis=1,
)  # .rename(columns={"Year": "Last measure"})

# Préparation du fichier final pour le Mix électrique mondial

mix = select.iloc[:, :4].copy()
mix["% Fossil"] = round(select.iloc[:, 4] / select.iloc[:, 10] * 100, 1)
mix["% Geothermal"] = round(select.iloc[:, 5] / select.iloc[:, 10] * 100, 1)
mix["% Hydro"] = round(select.iloc[:, 6] / select.iloc[:, 10] * 100, 1)
mix["% Nuclear"] = round(select.iloc[:, 7] / select.iloc[:, 10] * 100, 1)
mix["% Solar"] = round(select.iloc[:, 8] / select.iloc[:, 10] * 100, 1)
mix["% Wind"] = round(select.iloc[:, 9] / select.iloc[:, 10] * 100, 1)

default_ISO["% Fossil"] = "/"
default_ISO["% Geothermal"] = "/"
default_ISO["% Hydro"] = "/"
default_ISO["% Nuclear"] = "/"
default_ISO["% Solar"] = "/"
default_ISO["% Wind"] = "/"

mix = pd.concat([mix, default_ISO])

mix.to_csv("dashboard/WorldElectricityMix.csv", index=False)
