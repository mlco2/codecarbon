import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_table as dt
import fire
import pandas as pd
from dash.dependencies import Input, Output

from codecarbon.viz.components import Components
from codecarbon.viz.data import Data


def render_app(df: pd.DataFrame):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

    components = Components()
    header = components.get_header()
    net_summary = components.get_net_summary()
    project_dropdown = components.get_project_dropdown(df)
    project_details = components.get_project_details()
    exemplary_equivalents = components.get_exemplary_equivalents()
    _hidden_project_data = components.get_hidden_project_data()
    _hidden_project_summary = components.get_hidden_project_summary()
    cloud_emissions_comparison = components.get_cloud_emissions_comparison()
    global_comparison = components.get_global_comparison()
    regional_comparison = components.get_regional_emissions_comparison()
    project_time_series = components.get_project_time_series()
    project_emissions_bar_chart = components.get_project_emissions_bar_chart()
    references = components.get_references()

    data = Data()

    app.layout = dbc.Container(
        [
            header,
            net_summary,
            project_dropdown,
            project_details,
            exemplary_equivalents,
            cloud_emissions_comparison,
            global_comparison,
            regional_comparison,
            project_time_series,
            project_emissions_bar_chart,
            references,
            _hidden_project_data,
            _hidden_project_summary,
        ],
        style={"padding-top": "50px"},
    )

    @app.callback(
        [
            Output(component_id="hidden_project_data", component_property="children"),
            Output(component_id="hidden_project_summary", component_property="data"),
            Output(component_id="net_power_consumption", component_property="children"),
            Output(component_id="net_carbon_equivalent", component_property="children"),
            Output(
                component_id="project_infrastructure_location",
                component_property="children",
            ),
            Output(
                component_id="project_power_consumption", component_property="children"
            ),
            Output(
                component_id="project_carbon_equivalent", component_property="children"
            ),
            Output(
                component_id="last_run_power_consumption", component_property="children"
            ),
            Output(
                component_id="last_run_carbon_equivalent", component_property="children"
            ),
        ],
        [Input(component_id="project_name", component_property="value")],
    )
    def update_project_data(project_name: str):
        project_data = data.get_project_data(df, project_name)
        project_summary = data.get_project_summary(project_data.data)
        net_power_consumption = f"{'{:.1f}'.format(sum(df['energy_consumed']))} kWh"
        net_carbon_equivalent = f"{'{:.1f}'.format(sum(df['emissions']))} kg"
        if {project_summary["region"]} == "":
            project_infrastructure_location = f"{project_summary['country_name']}"
        else:
            project_infrastructure_location = (
                f"{project_summary['region']}, {project_summary['country_name']}"
            )
        project_power_consumption = (
            f"{round(project_summary['total']['energy_consumed'],1)} kWh"
        )
        project_carbon_equivalent = (
            f"{round(project_summary['total']['emissions'],1)} kg"
        )
        last_run_power_consumption = (
            f"{project_summary['last_run']['energy_consumed']} kWh"
        )
        last_run_carbon_equivalent = f"{project_summary['last_run']['emissions']} kg"

        return (
            project_data,
            project_summary,
            net_power_consumption,
            net_carbon_equivalent,
            project_infrastructure_location,
            project_power_consumption,
            project_carbon_equivalent,
            last_run_power_consumption,
            last_run_carbon_equivalent,
        )

    @app.callback(
        [
            Output(component_id="house_icon", component_property="src"),
            Output(component_id="car_icon", component_property="src"),
            Output(component_id="tv_icon", component_property="src"),
            Output(component_id="car_miles", component_property="children"),
            Output(component_id="tv_time", component_property="children"),
            Output(component_id="household_fraction", component_property="children"),
        ],
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_exemplary_equivalents(hidden_project_summary: dcc.Store):
        project_carbon_equivalent = hidden_project_summary["total"]["emissions"]
        house_icon = app.get_asset_url("house_icon.png")
        car_icon = app.get_asset_url("car_icon.png")
        tv_icon = app.get_asset_url("tv_icon.png")
        car_miles = f"{data.get_car_miles(project_carbon_equivalent)} miles"
        tv_time = data.get_tv_time(project_carbon_equivalent)
        household_fraction = (
            f"{data.get_household_fraction(project_carbon_equivalent)} %"
        )
        return house_icon, car_icon, tv_icon, car_miles, tv_time, household_fraction

    @app.callback(
        [
            Output(
                component_id="global_emissions_choropleth", component_property="figure"
            ),
            Output(
                component_id="global_energy_mix_choropleth", component_property="figure"
            ),
        ],
        [
            Input(component_id="hidden_project_summary", component_property="data"),
            Input(component_id="energy_type", component_property="value"),
        ],
    )
    def update_global_comparisons(hidden_project_summary: dcc.Store, energy_type: str):
        net_energy_consumed = hidden_project_summary["total"]["energy_consumed"]
        global_emissions_choropleth_data = data.get_global_emissions_choropleth_data(
            net_energy_consumed
        )

        return (
            components.get_global_emissions_choropleth_figure(
                global_emissions_choropleth_data
            ),
            components.get_global_energy_mix_choropleth_figure(
                energy_type, global_emissions_choropleth_data
            ),
        )

    @app.callback(
        Output(
            component_id="regional_emissions_comparison_component",
            component_property="style",
        ),
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_show_regional_comparison(hidden_project_summary: dcc.Store):
        country_iso_code = hidden_project_summary["country_iso_code"]
        # add country codes here to render for different countries
        if country_iso_code.upper() in ["USA", "CAN"]:
            return {"display": "block"}
        else:
            return {"display": "none"}

    @app.callback(
        [
            Output(component_id="country_name", component_property="children"),
            Output(
                component_id="regional_emissions_comparison_choropleth",
                component_property="figure",
            ),
        ],
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_regional_comparison_choropleth(hidden_project_summary: dcc.Store):
        country_name = hidden_project_summary["country_name"]
        country_iso_code = hidden_project_summary["country_iso_code"]
        net_energy_consumed = hidden_project_summary["total"]["energy_consumed"]
        regional_emissions_choropleth_data = (
            data.get_regional_emissions_choropleth_data(
                net_energy_consumed, country_iso_code
            )
        )

        return (
            country_name,
            components.get_regional_emissions_choropleth_figure(
                regional_emissions_choropleth_data, country_iso_code
            ),
        )

    @app.callback(
        Output(component_id="project_time_series", component_property="figure"),
        [Input(component_id="hidden_project_data", component_property="children")],
    )
    def update_project_time_series(hidden_project_data: dt.DataTable):
        return components.get_project_time_series_figure(
            hidden_project_data["props"]["data"]
        )

    @app.callback(
        Output(component_id="project_emissions_bar_chart", component_property="figure"),
        [Input(component_id="hidden_project_data", component_property="children")],
    )
    def update_project_time_series(hidden_project_data: dt.DataTable):
        return components.get_project_emissions_bar_chart_figure(
            hidden_project_data["props"]["data"]
        )

    @app.callback(
        Output(
            component_id="cloud_emissions_comparison_component",
            component_property="style",
        ),
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_on_cloud(hidden_project_summary: dcc.Store):
        on_cloud = hidden_project_summary["on_cloud"]
        if on_cloud == "Y":
            return {"display": "block"}
        else:
            return {"display": "none"}

    @app.callback(
        [
            Output(component_id="cloud_provider_name", component_property="children"),
            Output(
                component_id="cloud_emissions_barchart", component_property="figure"
            ),
            Output(component_id="cloud_recommendation", component_property="children"),
        ],
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_cloud_emissions_barchart(hidden_project_summary: dcc.Store):
        on_cloud = hidden_project_summary["on_cloud"]
        net_energy_consumed = hidden_project_summary["total"]["energy_consumed"]
        cloud_provider = hidden_project_summary["cloud_provider"]
        cloud_region = hidden_project_summary["cloud_region"]
        (
            cloud_provider_name,
            cloud_emissions_barchart_data,
        ) = data.get_cloud_emissions_barchart_data(
            net_energy_consumed, on_cloud, cloud_provider, cloud_region
        )

        return (
            cloud_provider_name,
            components.get_cloud_emissions_barchart_figure(
                cloud_emissions_barchart_data
            ),
            components.get_cloud_recommendation(
                on_cloud, cloud_provider_name, cloud_emissions_barchart_data
            ),
        )

    return app


def viz(filepath: str, port: int = 8050, debug: bool = False) -> None:
    df = pd.read_csv(filepath)
    app = render_app(df)
    app.run_server(port=port, debug=debug)


def main():
    fire.Fire(viz)


if __name__ == "__main__":
    main()
