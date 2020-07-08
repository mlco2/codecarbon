#!/usr/bin/env python


import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import fire
import pandas as pd
import plotly.express as px
import webbrowser
from threading import Timer


def compute_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    projects = df["project_name"].unique()
    return pd.DataFrame(
        {
            "Project": projects,
            "Mean Duration (seconds)": [
                df[df["project_name"] == project]["duration"].mean()
                for project in projects
            ],
            "Mean Emissions (kg)": [
                df[df["project_name"] == project]["emissions"].mean()
                for project in projects
            ],
        }
    )


def render_app(df: pd.DataFrame):
    summary_df = compute_summary_stats(df)
    table = dbc.Table.from_dataframe(
        summary_df, striped=True, bordered=True, hover=True
    )
    graph = dcc.Graph(
        figure=px.line(
            df, x="timestamp", y="emissions", template="seaborn", range_y=(0, 10)
        ),
    )

    baseline_card = [
        dbc.CardHeader("Baseline"),
        dbc.CardBody(
            [
                html.H5("Baseline Comparison", className="card-title"),
                html.P("1 kg of emissions are worth xyz", className="card-text",),
            ]
        ),
    ]

    placeholder_card = [
        dbc.CardHeader("Suggestion"),
        dbc.CardBody(
            [
                html.H5("Card title", className="card-title"),
                html.P("This is some card content", className="card-text", ),
            ]
        ),
    ]

    emissions_card = [
        dbc.CardHeader("Total Emissions"),
        dbc.CardBody(
            [
                html.P(
                    [
                        "Total emissions for all projects are ",
                        html.Strong(
                            "{} kg".format(df["emissions"].sum()),
                            style={"color": "green"},
                        ),
                    ],
                    className="card-text",
                )
            ]
        ),
    ]

    header = dbc.Jumbotron(
        [
            html.H1("CO2 Tracker", className="display-6"),
            html.P(
                "Machine Learning has a carbon footprint."
                " We've made a tool to help you estimate yours.",
                className="lead",
            ),
            html.Hr(className="my-4"),
            html.P(dbc.Button("Learn more", color="primary"), className="lead"),
        ],
    )

    content = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.CardDeck(
                            [
                                dbc.Card(emissions_card, color="primary", outline=True),
                                dbc.Card(
                                    baseline_card, color="primary", outline=True
                                ),
                                dbc.Card(
                                    placeholder_card, color="primary", outline=True
                                ),
                            ]
                        )
                    )
                ],
                style={"padding": "10px"},
                className="mb-4",
            ),
            dbc.Row([dbc.Col(graph)]),
            dbc.Row([dbc.Col(table)]),
        ]
    )

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
    app.layout = dbc.Container([header, content], style={"padding-top": "50px"},)
    return app


def open_browser():
    webbrowser.open_new("http://127.0.0.1:2000/")


def main(filename: str) -> None:
    df = pd.read_csv(filename)
    app = render_app(df)
    app.run_server(port=2000)


if __name__ == "__main__":
    Timer(1, open_browser).start()
    fire.Fire(main)
