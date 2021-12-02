import pandas as pd

# Read World Electricity Mix and EU Carbon Intensity
df1 = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/master/codecarbon/data/private_infra/eu-carbon-intensity-electricity.csv"
).rename(columns={"Entity": "Country"})

df2 = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/master/codecarbon/data/private_infra/world_energy_mix.csv"
).rename(columns={"country_name": "Country"})

# Merge the data per country and per year
df = pd.merge(df1, df2, on=["Country", "Year"], how="inner").drop(
    ["Unnamed: 0", "country_id"], axis=1
)
df["Total electricity generation"] = (
    df["Fossil fuels electricity generation"]
    + df["Geothermal electricity generation"]
    + df["Hydroelectricity generation"]
    + df["Nuclear power generation"]
    + df["Solar electricity generation"]
    + df["Wind electricity generation"]
)

# Filter on 2020 and calculate the corresponding ElectricityMix and CarbonIntensity for the selected countries
sel20 = df[df["Year"] == 2020]
sel_20 = sel20.iloc[:, :4].copy()
sel_20["% Fossil"] = round(sel20.iloc[:, 4] / sel20.iloc[:, 10] * 100, 1)
sel_20["% Geothermal"] = round(sel20.iloc[:, 5] / sel20.iloc[:, 10] * 100, 1)
sel_20["% Hydro"] = round(sel20.iloc[:, 6] / sel20.iloc[:, 10] * 100, 1)
sel_20["% Nuclear"] = round(sel20.iloc[:, 7] / sel20.iloc[:, 10] * 100, 1)
sel_20["% Solar"] = round(sel20.iloc[:, 8] / sel20.iloc[:, 10] * 100, 1)
sel_20["% Wind"] = round(sel20.iloc[:, 9] / sel20.iloc[:, 10] * 100, 1)

# Export the results to a final CSV file
sel_20.to_csv("dashboard/ElectricityMix.csv")
