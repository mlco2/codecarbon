from multiprocessing.sharedctypes import Value
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_table as dt
import fire
import pandas as pd
from dash.dependencies import Input, Output

from codecarbon.viz.components import Components
from codecarbon.viz.data import Data

from dash.exceptions import PreventUpdate

def render_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

    components = Components()
    header = components.get_header()
    experiment_input = components.get_experiment_input()
    runs_dropdown = components.get_runs_dropdown_component()
    test_div = components.get_test_div()
    experiment_details = components.get_experiment_details()

    data = Data()

    app.layout = dbc.Container(
        [
            header,
            experiment_input,
            runs_dropdown,
            test_div,
            experiment_details,
        ],
        style={"padding-top": "50px"},
    )

    @app.callback(
        [
            Output(
                component_id="last_run_power_consumption", component_property="children"
            ),
        ],
        [Input(component_id="run_name", component_property="value")],
    )
    def update_experiment_data(run_name: str):
        if not run_name:
            raise PreventUpdate
        run_data = data.get_run_data(run_name)
        run_summary = data.get_run_summary(run_data.data)
        last_run_power_consumption = (
            f"{run_summary['last_emission']['energy_consumed']} kWh"
        )
        return (
            last_run_power_consumption,
        )

    @app.callback(
        Output(component_id='test-result', component_property='children'),
        Input(component_id='run_name', component_property='value')
    )
    def update_test_div(run_name):
        return f"Result test is: {run_name}"

    @app.callback(
        Output(component_id="run_name", component_property="options"),
        [Input(component_id="experiment_name", component_property="value")],
    )
    def update_runs_dropdown_options(experiment_id: str):
        return components.get_runs_dropdown_options(experiment_id)

    return app


def viz(port: int = 8050, debug: bool = True) -> None:
    app = render_app()
    app.run_server(port=port, debug=debug)

def main():
    fire.Fire(viz)

if __name__ == "__main__":
    main()
