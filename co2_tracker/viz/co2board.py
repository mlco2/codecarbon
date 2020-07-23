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
        # getting the most frequently used location
        # may need to change later
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
    summary_df = compute_summary_stats(df).sort_values(by=['Project'])
    project_list = summary_df.get("Project").tolist()

    project_dropdown = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5(
                                "Project:",
                                style={
                                    "textAlign": "left",
                                    "fontWeight": "bold"
                                }
                            ),
                            dcc.Dropdown(
                                id="selected-project",
                                options=[{"label": i, "value": i} for i in project_list],
                                value=project_list[0]
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

    intl_mix = evaluate.get_data("../data/private_infra/2016/energy_mix.json")
    us_mix = evaluate.get_data("../data/private_infra/2016/energy_mix_us.json")
    us_data = evaluate.get_data("../data/private_infra/2016/us_emissions.json")

    country_list = sorted(intl_mix.keys())

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
                html.P(id="source1"),
                html.P(id="source2"),
                html.P(id="source3"),
                html.P(id="source4"),
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
                            style={"color": "green"},
                            id="equivalents-miles"
                        ),
                    ],
                ),
                html.P(
                    [
                        "Time of 32-in. LCD TV: ",
                        html.Strong(
                            style={"color": "green"},
                            id="equivalents-tv"
                        ),
                    ],
                ),
                html.P(
                    [
                        "% of CO",
                        html.Sub("2"),
                        " per US house/day: ",
                        html.Strong(
                            style={"color": "green"},
                            id="equivalents-home"
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
                                        style={"color": "green"},
                                        id="general-info-location",
                                    ),
                                ],
                            ),
                        ),
                        dbc.Col(
                            html.P(
                                [
                                    "Total kilowatt hours used: ",
                                    html.Strong(
                                        style={"color": "green"},
                                        id="general-info-kwh",
                                    ),
                                ],
                            ),
                        ),
                        dbc.Col(
                            html.P(
                                [
                                    "Total emissions for all projects: ",
                                    html.Strong(
                                        style={"color": "green"},
                                        id="general-info-emissions",
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
                            id = "energy-mix"
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
                    " emissions for the project if the computation had been performed elsewhere."
                ],
                style={
                    "textAlign": "center",
                }
            ),

            dcc.Graph(
                id="comparison-bar-charts"
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

    hidden_div = html.Div(id='intermediate-value', style={'display': 'none'})

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
    app.layout = dbc.Container([header, project_dropdown, cards, default_comparisons,
                                custom_comparison, graph_and_table, hidden_div],
                                style={"padding-top": "50px"},)

    # intermediate data
    @app.callback(
        Output("intermediate-value", "children"),
        [Input("selected-project", "value")])
    def update_project(project_name):
        project_row = summary_df.loc[lambda df: summary_df['Project'] == project_name]
        emissions = project_row.iloc[0,2]
        kwh = project_row.iloc[0,3]
        region = project_row.iloc[0,4]
        country = project_row.iloc[0,5]

        if country in ["United States"]:
            location = region
        else:
            location = country

        variables_df = pd.DataFrame(
            {
                "emissions": emissions,
                "kwh": kwh,
                "location": location
            },
            index=[0]
        )
        return variables_df.to_json()

    # general info, equivalents cards callback
    @app.callback(
        [Output('general-info-location', 'children'),
         Output('general-info-kwh', 'children'),
         Output('general-info-emissions', 'children'),
         Output('equivalents-miles', 'children'),
         Output('equivalents-tv', 'children'),
         Output('equivalents-home', 'children')],
        [Input('intermediate-value', 'children')])
    def update_cards(jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        emissions = dff.iloc[0, 0]
        kwh = dff.iloc[0, 1]
        location = dff.iloc[0, 2]

        general_info_location = "{} ".format(location)
        general_info_kwh = "{:.3g} kWh".format(kwh)
        general_info_emissions = "{:.3g} kg".format(emissions)

        equivalents_miles = "{:.2e} miles".format(convert.carbon_to_miles(emissions))
        equivalents_tv = convert.carbon_to_tv(emissions)
        equivalents_home = "{:.2e}%".format(convert.carbon_to_home(emissions))

        return (general_info_location, general_info_kwh, general_info_emissions,
                equivalents_miles, equivalents_tv, equivalents_home)

    # equivalencies card, energy mix graph callback
    @app.callback(
        [Output('source1', 'children'),
         Output('source2', 'children'),
         Output('source3', 'children'),
         Output('source4', 'children'),
         Output('energy-mix', 'figure')],
        [Input('intermediate-value', 'children')])
    def update_equivalencies_card(jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        location = dff.iloc[0, 2]

        if locate.in_US(location):
            energy_sources = ["Coal", "Oil", "Natural Gas", "Low Carbon"]
        else:
            energy_sources = ["Coal", "Petroleum", "Natural Gas", "Low Carbon"]

        source1 = [energy_sources[0] + ": ",
                html.Strong(["996 kg CO",html.Sub("2"),"/MWh"], style={"color": "green"})]
        source2 = [energy_sources[1] + ": ",
                html.Strong(["817 kg CO",html.Sub("2"),"/MWh"], style={"color": "green"})]
        source3 = [energy_sources[2] + ": ",
                html.Strong(["744 kg CO",html.Sub("2"),"/MWh"], style={"color": "green"})]
        source4 = [energy_sources[3] + ": ",
                html.Strong(["0 kg CO",html.Sub("2"),"/MWh"], style={"color": "green"})]

        energy_mix = report.energy_mix_graph(location, intl_mix, us_mix)
        return (source1, source2, source3, source4, energy_mix)

    # default comparison graphs callback
    @app.callback(
        Output('comparison-bar-charts', 'figure'),
        [Input('intermediate-value', 'children')])
    def update_default_comparison_graph(jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        emissions = dff.iloc[0, 0]
        kwh = dff.iloc[0, 1]
        location = dff.iloc[0, 2]
        fig = report.default_comparison_graphs(kwh, location, emissions, intl_mix, us_data)
        return fig

    # custom comparison graph callback
    @app.callback(
        Output("custom-comparison-graph", "figure"),
        [Input("selected-countries", "value"),
         Input("intermediate-value", "children")])
    def update_custom_comparison_graph(countries, jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        emissions = dff.iloc[0, 0]
        kwh = dff.iloc[0, 1]
        location = dff.iloc[0, 2]
        fig = report.custom_comparison_graph(kwh, location, emissions, countries, intl_mix, us_data)
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
