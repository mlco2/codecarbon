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

    def get_car_miles(self, project_carbon_equivalent: float):
        """
        8.89 × 10-3 metric tons CO2/gallon gasoline ×
        1/22.0 miles per gallon car/truck average ×
        1 CO2, CH4, and N2O/0.988 CO2
        = 4.09 x 10-4 metric tons CO2E/mile
        = 0.409 kg CO2E/mile
        Source: EPA
        :param project_carbon_equivalent: total project emissions in kg CO2E
        :return: number of miles driven by avg car
        """
        return "{:.2f}".format(project_carbon_equivalent / 0.409)

    def get_tv_time(self, project_carbon_equivalent: float):
        """
        Gives the amount of time
        a 32-inch LCD flat screen TV will emit
        an equivalent amount of carbon
        Ratio is 0.097 kg CO2 / 1 hour tv
        :param project_carbon_equivalent: total project emissions in kg CO2E
        :return: equivalent TV time
        """
        time_in_minutes = project_carbon_equivalent * (1 / 0.097) * 60
        formated_value = "{:.0f} minutes".format(time_in_minutes)
        if time_in_minutes >= 60:
            time_in_hours = time_in_minutes / 60
            formated_value = "{:.0f} hours".format(time_in_hours)
            if time_in_hours >= 24:
                time_in_days = time_in_hours / 24
                formated_value = "{:.0f} days".format(time_in_days)
        return formated_value

    def get_household_fraction(self, project_carbon_equivalent: float):
        """
        Total CO2 emissions for energy use per home: 5.734 metric tons CO2 for electricity
        + 2.06 metric tons CO2 for natural gas + 0.26 metric tons CO2 for liquid petroleum gas
         + 0.30 metric tons CO2 for fuel oil  = 8.35 metric tons CO2 per home per year / 52 weeks
         = 160.58 kg CO2/week on average
        Source: EPA
        :param project_carbon_equivalent: total project emissions in kg CO2E
        :return: % of weekly emissions re: an average American household
        """
        return "{:.2f}".format((project_carbon_equivalent / 160.58) * 100)

    def get_global_emissions_choropleth_data(
        self, net_energy_consumed: float
    ) -> List[Dict]:
        def formatted_energy_percentage(energy_type: float, total: float) -> float:
            return float("{:.1f}".format((energy_type / total) * 100))

        global_energy_mix = self.app_config.get_global_energy_mix_data()
        choropleth_data = []
        for country in global_energy_mix.keys():
            if country not in ["_define", "Antarctica"]:
                from co2_tracker.units import Energy

                energy_consumed = Energy.from_energy(kwh=net_energy_consumed)
                from co2_tracker.emissions import _get_country_emissions_energy_mix

                from co2_tracker.external.geography import GeoMetadata

                country_emissions = _get_country_emissions_energy_mix(
                    energy_consumed,
                    GeoMetadata(country),
                    self.app_config.global_energy_mix_data_path,
                )
                total = global_energy_mix[country]["total"]
                choropleth_data.append(
                    {
                        "iso_code": global_energy_mix[country]["isoCode"],
                        "emissions": country_emissions,
                        "country": country,
                        "coal": formatted_energy_percentage(
                            global_energy_mix[country]["coal"], total
                        ),
                        "petroleum": formatted_energy_percentage(
                            global_energy_mix[country]["petroleum"], total
                        ),
                        "natural_gas": formatted_energy_percentage(
                            global_energy_mix[country]["naturalGas"], total
                        ),
                        "low_carbon": formatted_energy_percentage(
                            global_energy_mix[country]["lowCarbon"], total
                        ),
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
