import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output
import fire
import pandas as pd

from co2_tracker.viz.components import Components
from co2_tracker.viz.data import Data


def render_app(df: pd.DataFrame):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

    components = Components()
    header = components.get_header()
    project_dropdown = components.get_project_dropdown(df)
    hidden_project_data = components.get_hidden_project_data()
    hidden_project_summary = components.get_hidden_project_summary()
    cloud_emissions_barchart = components.get_cloud_emissions_barchart()
    global_emissions_choropleth = components.get_global_emissions_choropleth()

    data = Data()

    app.layout = dbc.Container(
        [
            header,
            project_dropdown,
            cloud_emissions_barchart,
            global_emissions_choropleth,
            hidden_project_summary,
            hidden_project_data,
        ],
        style={"padding-top": "50px"},
    )

    @app.callback(
        [
            Output(component_id="hidden_project_data", component_property="children"),
            Output(component_id="hidden_project_summary", component_property="data"),
        ],
        [Input(component_id="project_name", component_property="value")],
    )
    def update_project_data(project_name: str):
        print(project_name)
        project_data = data.get_project_data(df, project_name)
        project_summary = data.get_project_summary(project_data.data)
        return project_data, project_summary

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
