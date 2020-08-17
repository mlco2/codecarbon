import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_table as dt
import fire
import pandas as pd

from co2_tracker.viz.components import Components
from co2_tracker.viz.data import Data


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
    cloud_emissions_barchart = components.get_cloud_emissions_barchart()
    global_emissions_choropleth = components.get_global_emissions_choropleth()
    project_time_series = components.get_project_time_series()

    data = Data()

    app.layout = dbc.Container(
        [
            header,
            net_summary,
            project_dropdown,
            project_details,
            exemplary_equivalents,
            cloud_emissions_barchart,
            global_emissions_choropleth,
            project_time_series,
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
        print(project_name)
        project_data = data.get_project_data(df, project_name)
        project_summary = data.get_project_summary(project_data.data)
        print(project_summary)
        net_power_consumption = f"{sum(df['energy_consumed'])} kWh"
        net_carbon_equivalent = f"{sum(df['emissions'])} kg"
        if {project_summary["region"]} == "":
            project_infrastructure_location = f"{project_summary['country']}"
        else:
            project_infrastructure_location = (
                f"{project_summary['region']}, {project_summary['country']}"
            )
        project_power_consumption = f"{project_summary['total']['energy_consumed']} kWh"
        project_carbon_equivalent = f"{project_summary['total']['emissions']} kg"
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
        Output(component_id="global_emissions_choropleth", component_property="figure"),
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_global_emissions_choropleth(hidden_project_summary: dcc.Store):
        net_energy_consumed = hidden_project_summary["total"]["energy_consumed"]
        global_emissions_choropleth_data = data.get_global_emissions_choropleth_data(
            net_energy_consumed
        )
        return components.get_global_emissions_choropleth_figure(
            global_emissions_choropleth_data
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
        Output(
            component_id="cloud_emissions_barchart_component",
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
        ],
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_cloud_emissions_barchart(hidden_project_summary: dcc.Store):
        on_cloud = hidden_project_summary["on_cloud"]
        net_energy_consumed = hidden_project_summary["total"]["energy_consumed"]
        cloud_provider = hidden_project_summary["cloud_provider"]
        cloud_region = hidden_project_summary["cloud_region"]
        cloud_provider_name, cloud_emissions_barchart_data = data.get_cloud_emissions_barchart_data(
            net_energy_consumed, on_cloud, cloud_provider, cloud_region
        )

        return (
            cloud_provider_name,
            components.get_cloud_emissions_barchart_figure(
                cloud_emissions_barchart_data
            ),
        )

    return app


def main(filename: str, port: int = 8050, debug: bool = False) -> None:
    df = pd.read_csv(filename)
    app = render_app(df)
    app.run_server(port=port, debug=debug)


if __name__ == "__main__":
    fire.Fire(main)
