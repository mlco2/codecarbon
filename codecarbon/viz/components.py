import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import numpy as np
import pandas as pd
import plotly.express as px
from dash.exceptions import PreventUpdate

from codecarbon.viz.data_loader import (
    load_experiment_runs,
)

class Components:
    def __init__(self):
        self.colorscale = [
            "rgb(0, 68, 27)",  # greens
            "rgb(0, 109, 44)",
            "rgb(35, 139, 69)",
            "rgb(65, 171, 93)",
            "rgb(116, 196, 118)",
            "rgb(161, 217, 155)",
            "rgb(199, 233, 192)",
            "rgb(229, 245, 224)",
            "rgb(240, 240, 240)",  # greys
            "rgb(217, 217, 217)",
            "rgb(189, 189, 189)",
            "rgb(253, 208, 162)",  # oranges
            "rgb(253, 174, 107)",
            "rgb(253, 141, 60)",
        ]  # px.colors.sequential.Greens_r,

    @staticmethod
    def get_test_div():
        return html.Div(id='test-result')

    @staticmethod
    def get_experiment_input():
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.H3("Experiment id", style={"textAlign": "left"}),
                    dcc.Input(
                        id="experiment_name",
                        type="text",
                        placeholder="0bfa2432-efda-4656-bdb4-f72d15866b0b",
                    ),
                ],
                style={"display": "inline-block"},
            )
        )

    @staticmethod
    def get_header():
        return dbc.Jumbotron(
            [
                html.H1("Carbon Footprint", style={"textAlign": "center"}),
                html.P(
                    "Measure Compute Emissions",
                    style={"textAlign": "center", "paddingLeft": "0.5%"},
                    className="lead",
                ),
            ]
        )


    @staticmethod
    def get_runs_dropdown_component():
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.H3("Select a run", style={"textAlign": "left"}),
                    dcc.Dropdown(id="run_name"),
                ],
                style={"display": "inline-block"},
            )
        )

    @staticmethod
    def get_runs_dropdown_options(experiment_id: str):
        if not experiment_id or len(experiment_id) != 36:
            raise PreventUpdate

        runs_from_api = load_experiment_runs(experiment_id)
        if not runs_from_api:
            raise PreventUpdate("Invalid experiment id")

        runs = [run['id'] for run in runs_from_api]
        options=[{"label": i, "value": i} for i in runs]
        return options


    @staticmethod
    def get_experiment_details():
        return html.Div(
            [
                html.Br(),
                html.Div(
                    [
                        html.H4(
                            [
                                "Last Emission Power Consumption : ",
                                html.Strong(
                                    id="last_run_power_consumption",
                                    style={"fontWeight": "normal", "color": "green"},
                                ),
                            ],
                            style={"float": "left"},
                        ),
                    ]
                ),
                html.Br(),
            ],
            style={"paddingLeft": "1.4%", "paddingRight": "1.4%"},
        )
