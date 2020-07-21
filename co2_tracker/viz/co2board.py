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
from dash.dependencies import Input, Output

import locate
import convert
import report
import evaluate


def compute_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    projects = df["project_name"].unique()
    country_dict = {}
    for project in projects:
        region = df[df["project_name"] == project]["region"].value_counts().idxmax()
        country = df[df["region"] == region]["country"].value_counts().idxmax()
        country_dict[project] = country

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
            "Mean Energy Usage (kWh)": [
                df[df["project_name"] == project]["total_energy_usage"].mean()
                for project in projects
            ],
            "Region": [
                df[df["project_name"] == project]["region"].value_counts().idxmax()
                for project in projects
            ],
            "Country": [
                country_dict[project]
                for project in projects
            ]
        }
    )


def render_app(df: pd.DataFrame):
    # dummy data
    country = "United States"
    state = "Pennsylvania"
    kwh = 3
    emissionsss = 1.68
    # END dummy data
    summary_df = compute_summary_stats(df)

    intl_mix = evaluate.get_data("../data/private_infra/2016/energy_mix.json")
    us_mix = evaluate.get_data("../data/private_infra/2016/energy_mix_us.json")
    us_data = evaluate.get_data("../data/private_infra/2016/us_emissions.json")

    country_list = sorted(intl_mix.keys())

    if country in ["United States"]:
        location = state
    else:
        location = country

    if locate.in_US(location):
        energy_sources = ["Coal", "Oil", "Natural Gas", "Low Carbon"]
    else:
        energy_sources = ["Coal", "Petroleum", "Natural Gas", "Low Carbon"]

    table = dbc.Table.from_dataframe(
        summary_df, striped=True, bordered=True, hover=True
    )
    graph = dcc.Graph(
        figure=px.line(
            df, x="timestamp", y="emissions", template="seaborn", range_y=(0, 10)
        ),
    )

    equivalencies_card = [
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

    equivalents_card = [
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
                        "Time of 32-in. LCD TV: ",
                        html.Strong(
                            convert.carbon_to_tv(emissionsss),
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

    general_info_card = [
        dbc.CardHeader(html.Strong("General Information")),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.P(
                                [
                                    "Location: ",
                                    html.Strong(
                                        "{} ".format(location),
                                        style={"color": "green"},
                                        id="location",
                                    ),
                                ],
                            ),
                        ),
                        dbc.Col(
                            html.P(
                                [
                                    "Total kilowatt hours used: ",
                                    html.Strong(
                                        "{} kWh".format(kwh),
                                        style={"color": "green"},
                                        id="kwh"
                                    ),
                                ],
                            ),
                        ),
                        dbc.Col(
                            html.P(
                                [
                                    "Total emissions for all projects: ",
                                    html.Strong(
                                        "{} kg".format(emissionsss),
                                        style={"color": "green"},
                                        id="emissions"
                                        ),
                                ],
                            )
                        )
                    ]
                )
            ],
            className="card-text",
        ),
    ]

    energy_mix_card = [
        dbc.CardHeader(html.Strong("Energy Mix Data")),
        dbc.CardBody(
            [
                dcc.Graph(
                    id = "energy-mix",
                    figure = report.energy_mix_graph(location, intl_mix, us_mix)
                )
            ]
        )
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
                        dbc.Card(
                            general_info_card, color="primary", outline=True
                        ),
                    ),
                ],
                style={"padding": "10px"},
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id = "energy-mix",
                            figure = report.energy_mix_graph(location, intl_mix, us_mix)
                        ),
                    ),
                    dbc.Col(
                        dbc.CardDeck(
                            [
                                dbc.Card(
                                    equivalencies_card, color="primary", outline=True
                                ),
                                dbc.Card(
                                    equivalents_card, color="primary", outline=True
                                ),
                            ]
                        ),
                    )
                ],
                style={"padding": "10px"},
                className="row align-items-center mb-4",
            ),

        ],
    )

    default_comparisons = html.Div(
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
                figure = report.default_comparison_graphs(kwh, location, emissionsss, intl_mix, us_data)
            )
        ]
    )

    custom_comparison = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(id="custom-comparison-graph")
                    ),
                    dbc.Col(
                        [
                            html.H5(
                                "Choose Locations:",
                                style={
                                    "textAlign": "left",
                                    "fontWeight": "bold"
                                }
                            ),
                            dcc.Dropdown(
                                id="selected-countries",
                                options=[{"label": i, "value": i} for i in country_list],
                                value=["Mongolia", "Iceland", "Switzerland"],
                                multi=True
                            )
                        ],
                        style={"display": "inline-block"}
                    )
                ],
                style={"padding": "10px"},
                className="row align-items-center mb-4",
            )
        ]
    )

    graph_and_table = html.Div(
        [
            html.H3(
                "Emission Time Series",
                style={
                    "textAlign": "center",
                    "fontWeight": "bold"
                }
            ),
            dbc.Row([dbc.Col(graph)]),
            dbc.Row([dbc.Col(table)]),
        ]
    )

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
    app.layout = dbc.Container([header, cards, default_comparisons,
                                custom_comparison, graph_and_table],
                            style={"padding-top": "50px"},)

    @app.callback(
        Output("custom-comparison-graph", "figure"),
        [Input("selected-countries", "value")])
    def update_graph(countries):
        fig = report.custom_comparison_graph(kwh, location, emissionsss, countries, intl_mix, us_data)
        return fig

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
