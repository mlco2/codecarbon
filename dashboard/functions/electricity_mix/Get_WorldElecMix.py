import pandas as pd

# Lire le World Energy Mix (last version)
df1 = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/master/codecarbon/data/private_infra/world_energy_mix.csv"
).rename(columns={"country_name": "Country"})

# Lire les codes pays associés aux intensités carbone (2020)
df2 = pd.read_csv("dashboard/functions/electricity_mix/WorldIntensity.csv").rename(
    columns={"CarbonIntensity": "Carbon intensity of electricity (gCO2/kWh)"}
)
df2.iloc[:, 2] = round(df2.iloc[:, 2], 0)

# All countries in 2019 with medium wolrd C02 intensity (475)
df = pd.merge(df2, df1, on=["Country"], how="right")

df = df.drop(["Unnamed: 0", "country_id"], axis=1)
df["Total electricity generation"] = (
    df["Fossil fuels electricity generation"]
    + df["Geothermal electricity generation"]
    + df["Hydroelectricity generation"]
    + df["Nuclear power generation"]
    + df["Solar electricity generation"]
    + df["Wind electricity generation"]
)

sel19 = df[df["Year"] == 2019]

sel_19 = sel19.iloc[:, :4].copy()
sel_19["% Fossil"] = round(sel19.iloc[:, 4] / sel19.iloc[:, 10] * 100, 1)
sel_19["% Geothermal"] = round(sel19.iloc[:, 5] / sel19.iloc[:, 10] * 100, 1)
sel_19["% Hydro"] = round(sel19.iloc[:, 6] / sel19.iloc[:, 10] * 100, 1)
sel_19["% Nuclear"] = round(sel19.iloc[:, 7] / sel19.iloc[:, 10] * 100, 1)
sel_19["% Solar"] = round(sel19.iloc[:, 8] / sel19.iloc[:, 10] * 100, 1)
sel_19["% Wind"] = round(sel19.iloc[:, 9] / sel19.iloc[:, 10] * 100, 1)

sel_19.to_csv("dashboard/WorldElectricityMix.csv", index=False)
