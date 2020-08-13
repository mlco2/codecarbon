import dash_table as dt
import pandas as pd
from typing import List, Dict, Tuple

from co2_tracker.config import AppConfig


class Data:
    def __init__(self):
        self.app_config = AppConfig()

    @staticmethod
    def get_project_data(df: pd.DataFrame, project_name) -> dt.DataTable:
        project_df = df[df.project_name == project_name]
        project_df = project_df.sort_values(by="timestamp")
        project_data = project_df.to_dict("rows")
        columns = [{"name": column, "id": column} for column in project_df.columns]
        return dt.DataTable(data=project_data, columns=columns)

    @staticmethod
    def get_project_summary(project_data: List[Dict]):
        last_run = project_data[-1]
        project_summary = {
            "last_run": {
                "timestamp": last_run["timestamp"],
                "duration": last_run["duration"],
                "emissions": last_run["emissions"],
                "energy_consumed": last_run["energy_consumed"],
            },
            "total": {
                "duration": sum(
                    map(lambda experiment: experiment["duration"], project_data)
                ),
                "emissions": sum(
                    map(lambda experiment: experiment["emissions"], project_data)
                ),
                "energy_consumed": sum(
                    map(lambda experiment: experiment["energy_consumed"], project_data)
                ),
            },
            "country": last_run["country"],
            "region": last_run["region"],
            "on_cloud": last_run["on_cloud"],
            "cloud_provider": last_run["cloud_provider"],
            "cloud_region": last_run["cloud_region"],
        }
        return project_summary

    def get_global_emissions_choropleth_data(
        self, net_energy_consumed: float
    ) -> List[Dict]:
        global_energy_mix = self.app_config.get_global_energy_mix_data()
        choropleth_data = []
        for country in global_energy_mix.keys():
            if country != "_define":
                from co2_tracker.units import Energy

                energy_consumed = Energy.from_energy(kwh=net_energy_consumed)
                from co2_tracker.emissions import _get_country_emissions_energy_mix

                from co2_tracker.external.geography import GeoMetadata

                country_emissions = _get_country_emissions_energy_mix(
                    energy_consumed,
                    GeoMetadata(country),
                    self.app_config.global_energy_mix_data_path,
                )
                choropleth_data.append(
                    {
                        "iso_code": global_energy_mix[country]["isoCode"],
                        "emissions": country_emissions,
                        "country": country,
                    }
                )
        return choropleth_data

    def get_cloud_emissions_barchart_data(
        self,
        net_energy_consumed: float,
        on_cloud: str,
        cloud_provider: str,
        cloud_region: str,
    ) -> Tuple[str, pd.DataFrame]:
        if on_cloud == "N":
            return "", pd.DataFrame(data={"region": [], "emissions": [], "country": []})
        cloud_emissions = self.app_config.get_cloud_emissions_data()
        cloud_emissions = cloud_emissions[
            ["provider", "providerName", "region", "impact", "country"]
        ]

        from co2_tracker.units import CO2EmissionsPerKwh

        cloud_emissions["emissions"] = cloud_emissions.apply(
            lambda row: CO2EmissionsPerKwh.from_g_per_kwh(row.impact).kgs_per_kwh
            * net_energy_consumed,
            axis=1,
        )

        cloud_emissions_project_region = cloud_emissions[
            cloud_emissions.region == cloud_region
        ]
        cloud_emissions = cloud_emissions[
            (cloud_emissions.provider == cloud_provider)
            & (cloud_emissions.region != cloud_region)
        ].sort_values(by="emissions")

        return (
            cloud_emissions_project_region.iloc[0, :].providerName,
            pd.concat([cloud_emissions_project_region, cloud_emissions]),
        )
