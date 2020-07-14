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

import locate
import convert
import evaluate


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
    # dummy data
    location = "Pennsylvania"
    kwh = 3
    emissionsss = 1.68
    # END dummy data

    if locate.in_US(location):
        state_emission = True
        energy_sources = ["Coal", "Oil", "Natural Gas", "Low Carbon"]
    else:
        state_emission = False
        energy_sources = ["Coal", "Petroleum", "Natural Gas", "Low Carbon"]

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
        dbc.CardHeader(html.Strong("Assumed Carbon Equivalencies")),
        dbc.CardBody(
            [
                html.P(
                    [
                        energy_sources[0] + ": ",
                        html.Strong(
                            [
                                "996 kg CO",
                                html.Sub("2"),
                                "/MWh"
                            ],
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        energy_sources[1] + ": ",
                        html.Strong(
                            [
                                "817 kg CO",
                                html.Sub("2"),
                                "/MWh"
                            ],
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        energy_sources[2] + ": ",
                        html.Strong(
                            [
                                "744 kg CO",
                                html.Sub("2"),
                                "/MWh"
                            ],
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        energy_sources[3] + ": ",
                        html.Strong(
                            [
                                "0 kg CO",
                                html.Sub("2"),
                                "/MWh"
                            ],
                            style={"color": "green"},
                        ),
                    ],
                ),
            ],
            className="card-text",
        ),
    ]

    placeholder_card = [
        dbc.CardHeader(html.Strong(["CO", html.Sub("2"), " Emissions Equivalents"])),
        dbc.CardBody(
            [
                html.P(
                    [
                        "Miles driven: ",
                        html.Strong(
                            "{:.2e} miles".format(convert.carbon_to_miles(emissionsss)),
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        "Min. of 32-in. LCD TV: ",
                        html.Strong(
                            "{:.2e} minutes".format(convert.carbon_to_tv(emissionsss)),
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        "% of CO",
                        html.Sub("2"),
                        " per US house/day: ",
                        html.Strong(
                            "{:.2e}%".format(convert.carbon_to_home(emissionsss)),
                            style={"color": "green"},
                        ),
                    ],
                ),
            ],
            className="card-text",
        ),
    ]

    emissions_card = [
        dbc.CardHeader(html.Strong("General Information")),
        dbc.CardBody(
            [
                html.P(
                    [
                        "Location: ",
                        html.Strong(
                            "{} ".format(location),
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        "Total kilowatt hours used: ",
                        html.Strong(
                            "{} kWh".format(kwh),
                            style={"color": "green"},
                        ),
                    ],
                ),
                html.P(
                    [
                        "Total emissions for all projects: ",
                        html.Strong(
                            "{} kg".format(emissionsss),
                            style={"color": "green"},
                        ),
                    ],
                )

            ],
            className="card-text",
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

    cards = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.CardDeck(
                            [
                                dbc.Card(
                                    emissions_card, color="primary", outline=True
                                ),
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

        ],
    )

    comparisons = html.Div(
        [
            html.H3(
                "Emission Comparisons",
                style={
                    "textAlign": "center",
                    "fontWeight": "bold"
                }
            ),

            html.Div(
                [
                    "CO",
                    html.Sub("2"),
                    " emissions for the projects if the computation had been performed elsewhere."
                ],
                style={
                    "textAlign": "center",
                }
            ),

            dcc.Graph(
                id = "comparison-bar-charts",
                figure = evaluate.comparison_graphs(kwh, location, emissionsss)
            )
        ]
    )

    graph_and_table = html.Div(
        [
            dbc.Row([dbc.Col(graph)]),
            dbc.Row([dbc.Col(table)]),
        ]
    )



    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
    app.layout = dbc.Container([header, cards, comparisons, graph_and_table], style={"padding-top": "50px"},)
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
