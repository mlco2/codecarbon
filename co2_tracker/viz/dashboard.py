import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output

import dash_table as dt
import fire
import pandas as pd

from co2_tracker.viz.components import Components
from co2_tracker.viz.choropleth import Choropleth


def render_app(df: pd.DataFrame):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

    components = Components()
    header = components.get_header()
    project_dropdown = components.get_project_dropdown(df)
    hidden_project_data = components.get_hidden_project_data()
    hidden_project_summary = components.get_hidden_project_summary()

    choropleth = Choropleth()
    global_emissions_choropleth = choropleth.get_global_emissions_choropleth()

    app.layout = dbc.Container(
        [
            header,
            project_dropdown,
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
        project_df = df[df.project_name == project_name]
        project_df = project_df.sort_values(by="timestamp")
        data = project_df.to_dict("rows")
        columns = [{"name": column, "id": column} for column in project_df.columns]
        project_summary = components.get_project_summary(project_df)
        return dt.DataTable(data=data, columns=columns), project_summary

    @app.callback(
        Output(component_id="global_emissions_choropleth", component_property="figure"),
        [Input(component_id="hidden_project_summary", component_property="data")],
    )
    def update_global_emissions_choropleth(hidden_project_summary: dcc.Store):
        net_energy_consumed = hidden_project_summary["total"]["energy_consumed"]
        choropleth_data = choropleth.get_global_emissions_choropleth_data(
            net_energy_consumed
        )
        return choropleth.get_global_emissions_choropleth_figure(choropleth_data)

    return app


def main(filename: str, port: int = 8050, debug: bool = False) -> None:
    df = pd.read_csv(filename)
    app = render_app(df)
    app.run_server(port=port, debug=debug)


if __name__ == "__main__":
    # Timer(1, open_browser).start()
    fire.Fire(main)
