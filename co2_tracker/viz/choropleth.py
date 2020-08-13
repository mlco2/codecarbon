import dash_core_components as dcc
import plotly.express as px

from co2_tracker.config import AppConfig


class Choropleth:
    @staticmethod
    def get_global_emissions_choropleth_figure(choropleth_data):
        fig = px.choropleth(
            choropleth_data,
            locations="iso_code",
            color="emissions",
            hover_name="iso_code",
            labels={"iso_code": "Country", "emissions": "Carbon Equivalent (kg)"},
            color_continuous_scale=px.colors.sequential.Greens_r,
        )
        return fig

    @staticmethod
    def get_global_emissions_choropleth():
        return dcc.Graph(id="global_emissions_choropleth")

    @staticmethod
    def get_global_emissions_choropleth_data(net_energy_consumed):
        app_config = AppConfig()
        global_energy_mix = app_config.get_global_energy_mix_data()
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
                    app_config.global_energy_mix_data_path,
                )
                choropleth_data.append(
                    {
                        "iso_code": global_energy_mix[country]["isoCode"],
                        "emissions": country_emissions,
                        "country": country,
                    }
                )
        return choropleth_data
