#!/usr/bin/env python


import dash
import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import fire
import pandas as pd
import plotly.express as px
import webbrowser
from threading import Timer
from dash.dependencies import Input, Output

import convert, evaluate, report


def compute_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    projects = df["project_name"].unique()
    country_dict = {}
    for project in projects:
        # getting the most frequently used location, may need to change later
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
                df[df["project_name"] == project]["energy_consumed"].mean()
                for project in projects
            ],
            "Region": [
                df[df["project_name"] == project]["region"].value_counts().idxmax()
                for project in projects
            ],
            "Country": [country_dict[project] for project in projects],
        }
    )


def render_app(df: pd.DataFrame):
    summary_df = compute_summary_stats(df).sort_values(by=["Project"])
    project_list = summary_df.get("Project").tolist()

    project_dropdown = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5(
                                "Project:",
                                style={"textAlign": "left", "fontWeight": "bold"},
                            ),
                            dcc.Dropdown(
                                id="selected-project",
                                options=[
                                    {"label": i, "value": i} for i in project_list
                                ],
                                value=project_list[0],
                            ),
                        ],
                        style={"display": "inline-block"},
                    )
                ],
                style={"padding": "10px"},
                className="row align-items-center mb-4",
            )
        ]
    )

    intl_mix = evaluate.get_intl_energy_mix()
    us_mix, canada_mix = evaluate.get_country_energy_mix()

    countries_with_direct_emissions = {"United States": us_mix, "Canada": canada_mix}
    countries_with_regional_energy_mix = ["United States", "Canada"]

    country_list = sorted(intl_mix.keys())

    table = dbc.Table.from_dataframe(
        summary_df, striped=True, bordered=True, hover=True
    )
    graph = dcc.Graph(
        figure=px.line(df, x="timestamp", y="emissions", template="seaborn")
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
                        html.Img(id="car-img"),
                        "Miles driven: ",
                        html.Strong(style={"color": "green"}, id="equivalents-miles"),
                    ]
                ),
                html.P(
                    [
                        html.Img(id="tv-img"),
                        "Time of 32-in. LCD TV: ",
                        html.Strong(style={"color": "green"}, id="equivalents-tv"),
                    ]
                ),
                html.P(
                    [
                        html.Img(id="house-img"),
                        "% of CO",
                        html.Sub("2"),
                        " per US house/day: ",
                        html.Strong(style={"color": "green"}, id="equivalents-home"),
                    ]
                ),
                html.P(html.Br()),
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
                                ]
                            )
                        ),
                        dbc.Col(
                            html.P(
                                [
                                    "Total kilowatt hours used: ",
                                    html.Strong(
                                        style={"color": "green"}, id="general-info-kwh"
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            html.P(
                                [
                                    "Total emissions for all projects: ",
                                    html.Strong(
                                        style={"color": "green"},
                                        id="general-info-emissions",
                                    ),
                                ]
                            )
                        ),
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
            html.P(
                [
                    "For more information on the methodology used to calculate ",
                    "these results, see: ",
                    html.A(
                        "mlco2 paper",
                        href="https://arxiv.org/pdf/1910.09700.pdf",
                        target="_blank",
                    ),
                    " and ",
                    html.A(
                        "energy-usage paper",
                        href="https://arxiv.org/pdf/1911.08354.pdf",
                        target="_blank",
                    ),
                    ".",
                ]
            ),
        ]
    )

    cards = html.Div(
        [
            dbc.Row(
                [dbc.Col(dbc.Card(general_info_card, color="primary", outline=True))],
                style={"padding": "10px"},
                className="mb-0",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(equivalencies_card, color="primary", outline=True)
                    ),
                    dbc.Col([dcc.Graph(id="energy-mix")]),
                    dbc.Col(dbc.Card(equivalents_card, color="primary", outline=True)),
                ],
                style={"padding": "10px"},
                className="row align-items-center mb-0",
            ),
        ]
    )

    default_comparisons = html.Div(
        [
            html.H3(
                "Emission Comparisons",
                style={"textAlign": "center", "fontWeight": "bold"},
            ),
            html.Div(id="emission-comparisons-header", style={"textAlign": "left"}),
            dcc.Graph(id="comparison-bar-charts"),
        ]
    )

    custom_comparison = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="custom-comparison-graph")),
                    dbc.Col(
                        [
                            html.H5(
                                "Select Countries:",
                                style={"textAlign": "left", "fontWeight": "400"},
                            ),
                            dcc.Dropdown(
                                id="selected-countries",
                                value=["Mongolia", "Iceland", "Switzerland"],
                                multi=True,
                            ),
                            html.H5(
                                "Select Regions:",
                                style={
                                    "textAlign": "left",
                                    "fontWeight": "400",
                                    "padding-top": "10px",
                                },
                            ),
                            dcc.Dropdown(id="selected-regions", value=[], multi=True),
                        ],
                        style={"display": "inline-block"},
                    ),
                ],
                style={"padding": "10px"},
                className="row align-items-center mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5(
                                id="chosen-region-pie-title",
                                style={"textAlign": "center", "fontWeight": "600"},
                            ),
                            dcc.Graph(id="chosen-region-pie"),
                        ]
                    ),
                    dbc.Col(
                        [
                            html.H5(
                                "Selected Locations Energy Mix",
                                style={"textAlign": "center", "fontWeight": "600"},
                            ),
                            dash_table.DataTable(
                                id="energy-mix-table",
                                columns=[
                                    {
                                        "name": "Location",
                                        "id": "location",
                                        "deletable": False,
                                        "renamable": False,
                                    },
                                    {
                                        "name": "Coal",
                                        "id": "coal",
                                        "deletable": False,
                                        "renamable": False,
                                    },
                                    {
                                        "name": "Oil/Petroleum",
                                        "id": "oil-petroleum",
                                        "deletable": False,
                                        "renamable": False,
                                    },
                                    {
                                        "name": "Natural Gas",
                                        "id": "natural-gas",
                                        "deletable": False,
                                        "renamable": False,
                                    },
                                    {
                                        "name": "Low Carbon",
                                        "id": "low-carbon",
                                        "deletable": False,
                                        "renamable": False,
                                    },
                                ],
                                editable=False,
                            ),
                        ]
                    ),
                ],
                style={"padding": "10px"},
                className="row align-items-center mb-2",
            ),
        ]
    )

    graph_and_table = html.Div(
        [
            html.H3(
                "Emissions Time Series",
                style={"textAlign": "center", "fontWeight": "bold"},
            ),
            dbc.Row([dbc.Col(graph)], className="row mb-2"),
            dbc.Row([dbc.Col(table)], className="row mb-4"),
        ]
    )

    emoticon_credit = html.P(
        [
            "All emojis designed by and remixed from ",
            html.A("OpenMoji ", href="https://openmoji.org/", target="_blank"),
            "– the open-source emoji and icon project. License: ",
            html.A(
                "CC BY-SA 4.0",
                href="https://creativecommons.org/licenses/by-sa/4.0/#",
                target="_blank",
            ),
        ]
    )

    hidden_div1 = html.Div(id="intermediate-value", style={"display": "none"})
    hidden_div2 = html.Div(id="countries-dropdown-data", style={"display": "none"})

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
    app.layout = dbc.Container(
        [
            header,
            project_dropdown,
            cards,
            default_comparisons,
            custom_comparison,
            graph_and_table,
            emoticon_credit,
            hidden_div1,
            hidden_div2,
        ],
        style={"padding-top": "50px"},
    )

    # intermediate data
    @app.callback(
        [
            Output("intermediate-value", "children"),
            Output("emission-comparisons-header", "children"),
            Output("selected-countries", "options"),
        ],
        [Input("selected-project", "value")],
    )
    def update_project(project_name):
        project_row = summary_df.loc[lambda df: summary_df["Project"] == project_name]
        emissions = project_row.iloc[0, 2]
        kwh = project_row.iloc[0, 3]
        region = project_row.iloc[0, 4]
        country = project_row.iloc[0, 5]

        variables_df = pd.DataFrame(
            {"emissions": emissions, "kwh": kwh, "region": region, "country": country},
            index=[0],
        )

        min_place, min_emissions = evaluate.get_min_place_and_emissions(kwh)
        emissions_difference = round(emissions - min_emissions, 2)
        emissions_comparisons_header = [
            html.P(
                [
                    "One of the main things you can do to reduce your CO",
                    html.Sub("2"),
                    " emissions is to run your code at a place with a more ",
                    "environmentally friendly energy mix. ",
                    "Below you can see the CO",
                    html.Sub("2"),
                    " emissions for the project if the computation had been ",
                    "performed elsewhere (min, median, and max are included ",
                    "for each region). For example, if you ran your code in ",
                    html.Strong(min_place),
                    ", you could reduce your CO",
                    html.Sub("2"),
                    " emissions by ",
                    html.Strong([emissions_difference, " kg!"]),
                ],
                className="mb-2",
            ),
            html.P(
                [
                    "In the bottom chart you can explore what would happen ",
                    "if you moved your computation to various places around the ",
                    "world.",
                ],
                className="mb-2",
            ),
        ]

        # remove location country from country dropdown if no regional mix
        if (
            country not in countries_with_regional_energy_mix
            and country in country_list
        ):
            country_list.remove(country)
        country_options = [{"label": i, "value": i} for i in country_list]

        return variables_df.to_json(), emissions_comparisons_header, country_options

    # general info, equivalents cards callback
    @app.callback(
        [
            Output("general-info-location", "children"),
            Output("general-info-kwh", "children"),
            Output("general-info-emissions", "children"),
            Output("equivalents-miles", "children"),
            Output("equivalents-tv", "children"),
            Output("equivalents-home", "children"),
        ],
        [Input("intermediate-value", "children")],
    )
    def update_cards(jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        emissions = dff.iloc[0, 0]
        kwh = dff.iloc[0, 1]
        region = dff.iloc[0, 2]
        country = dff.iloc[0, 3]

        if country in countries_with_regional_energy_mix:
            location = region
        else:
            location = country

        general_info_location = "{} ".format(location)
        general_info_kwh = "{:.3g} kWh".format(kwh)
        general_info_emissions = ["{:.3g} kg CO".format(emissions), html.Sub("2")]

        equivalents_miles = f"{convert.carbon_to_miles(emissions)} miles"
        equivalents_tv = convert.carbon_to_tv(emissions)
        equivalents_home = f"{convert.carbon_to_home(emissions)} %"

        return (
            general_info_location,
            general_info_kwh,
            general_info_emissions,
            equivalents_miles,
            equivalents_tv,
            equivalents_home,
        )

    # equivalencies card, energy mix graph callback
    @app.callback(
        [
            Output("source1", "children"),
            Output("source2", "children"),
            Output("source3", "children"),
            Output("source4", "children"),
            Output("energy-mix", "figure"),
            Output("car-img", "src"),
            Output("car-img", "alt"),
            Output("car-img", "width"),
            Output("car-img", "height"),
            Output("tv-img", "src"),
            Output("tv-img", "alt"),
            Output("tv-img", "width"),
            Output("tv-img", "height"),
            Output("house-img", "src"),
            Output("house-img", "alt"),
            Output("house-img", "width"),
            Output("house-img", "height"),
        ],
        [Input("intermediate-value", "children")],
    )
    def update_equivalencies_card(jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        region = dff.iloc[0, 2]
        country = dff.iloc[0, 3]

        # carbon equivalencies card
        if country == "united States":
            energy_sources = ["Coal", "Oil", "Natural Gas", "Low Carbon"]
        else:
            energy_sources = ["Coal", "Petroleum", "Natural Gas", "Low Carbon"]

        source1 = [
            html.Img(
                src=app.get_asset_url("mountain_pickax.png"),
                alt="coal image",
                width="32",
                height="32",
            ),
            "{}: ".format(energy_sources[0]),
            html.Strong(["996 kg CO", html.Sub("2"), "/MWh"], style={"color": "green"}),
        ]
        source2 = [
            html.Img(
                src=app.get_asset_url("oil.png"),
                alt="oil/petroleum image",
                width="32",
                height="32",
            ),
            "{}: ".format(energy_sources[1]),
            html.Strong(["817 kg CO", html.Sub("2"), "/MWh"], style={"color": "green"}),
        ]
        source3 = [
            html.Img(
                src=app.get_asset_url("natural_gas.png"),
                alt="natural gas image",
                width="32",
                height="32",
            ),
            "{}: ".format(energy_sources[2]),
            html.Strong(["744 kg CO", html.Sub("2"), "/MWh"], style={"color": "green"}),
        ]
        source4 = [
            html.Img(
                src=app.get_asset_url("low_carbon.png"),
                alt="low carbon image",
                width="32",
                height="32",
            ),
            "{}: ".format(energy_sources[3]),
            html.Strong(["0 kg CO", html.Sub("2"), "/MWh"], style={"color": "green"}),
        ]

        # energy mix graph
        if country in countries_with_regional_energy_mix:
            location = region
        else:
            location = country
        energy_mix = report.energy_mix_graph(
            location, countries_with_regional_energy_mix
        )

        # carbon equivalents card
        car_img_src = app.get_asset_url("car.png")
        car_img_alt, car_img_width, car_img_height = "car image", "32", "32"
        tv_img_src = app.get_asset_url("tv.png")
        tv_img_alt, tv_img_width, tv_img_height = "tv image", "32", "32"
        house_img_src = app.get_asset_url("house_with_tree.png")
        house_img_alt, house_img_width, house_img_height = "house image", "32", "32"
        return (
            source1,
            source2,
            source3,
            source4,
            energy_mix,
            car_img_src,
            car_img_alt,
            car_img_width,
            car_img_height,
            tv_img_src,
            tv_img_alt,
            tv_img_width,
            tv_img_height,
            house_img_src,
            house_img_alt,
            house_img_width,
            house_img_height,
        )

    # default comparison graphs callback
    @app.callback(
        Output("comparison-bar-charts", "figure"),
        [Input("intermediate-value", "children")],
    )
    def update_default_comparison_graph(jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        emissions = dff.iloc[0, 0]
        kwh = dff.iloc[0, 1]
        region = dff.iloc[0, 2]
        country = dff.iloc[0, 3]

        if country in countries_with_direct_emissions:
            location = region
        else:
            location = country

        fig = report.default_comparison_graphs(kwh, location, emissions)
        return fig

    # intermediate data for custom comparison graph region dropdown
    @app.callback(
        [
            Output("countries-dropdown-data", "children"),
            Output("selected-regions", "options"),
        ],
        [Input("selected-countries", "value"), Input("intermediate-value", "children")],
    )
    def update_regions_dropdown(countries, jsonified_variables):
        dff = pd.read_json(jsonified_variables)
        region = dff.iloc[0, 2]

        regions = []
        for country in countries:
            if country in countries_with_direct_emissions:
                regions_in_country = list(
                    countries_with_direct_emissions[country].keys()
                )
                if region in regions_in_country:
                    regions_in_country.remove(region)
                regions.extend(
                    list(map(lambda x: "{}/{}".format(country, x), regions_in_country))
                )

        if regions == []:
            regions.append("No Regions Available")
            region_dropdown_data = [
                {"label": i, "value": i, "disabled": True} for i in regions
            ]
        else:
            regions = sorted(regions)
            region_dropdown_data = [{"label": i, "value": i} for i in regions]

        countries_df = pd.DataFrame({"countries": countries})
        return countries_df.to_json(), region_dropdown_data

    # custom comparison graph country dropdown callback
    @app.callback(
        [
            Output("custom-comparison-graph", "figure"),
            Output("chosen-region-pie-title", "children"),
            Output("chosen-region-pie", "figure"),
            Output("energy-mix-table", "data"),
        ],
        [
            Input("countries-dropdown-data", "children"),
            Input("selected-regions", "value"),
            Input("intermediate-value", "children"),
        ],
    )
    def update_custom_comparison_graph(countries, regions, jsonified_variables):
        countries_df = pd.read_json(countries)
        countries = countries_df["countries"].tolist()
        dff = pd.read_json(jsonified_variables)
        emissions = dff.iloc[0, 0]
        kwh = dff.iloc[0, 1]
        region = dff.iloc[0, 2]
        country = dff.iloc[0, 3]

        # custom comparison graph
        if country in countries_with_direct_emissions:
            location = region
        else:
            location = country

        if regions != ["No Regions Available"]:
            regions = [x for x in regions if x.split("/")[0] in countries]
            if regions == []:
                locations = countries
            else:
                locations = countries + list(map(lambda x: x.split("/")[1], regions))
                countries_with_regions = list(
                    set(list(map(lambda x: x.split("/")[0], regions)))
                )
                # remove country from graphs & table if user selects a region
                for country in countries_with_regions:
                    locations.remove(country)
        else:
            locations = countries

        fig = report.custom_comparison_graph(kwh, location, emissions, locations)

        # energy mix table
        mix_data = []
        for location in locations:
            labels, values = report.energy_mix_data(
                location, countries_with_regional_energy_mix
            )
            if location == locations[-1]:
                most_recent_mix_graph = report.energy_mix_graph(
                    location, countries_with_regional_energy_mix
                )
                chosen_region_pie_title = "Energy Mix: {}".format(location)
            mix_data.append(
                {
                    "location": location,
                    "coal": "{}%".format(values[0]),
                    "oil-petroleum": "{}%".format(values[1]),
                    "natural-gas": "{}%".format(values[2]),
                    "low-carbon": "{}%".format(values[3]),
                }
            )

        return fig, chosen_region_pie_title, most_recent_mix_graph, mix_data

    return app


# def open_browser():
#     webbrowser.open_new("http://127.0.0.1:2000/")


def main(filename: str) -> None:
    df = pd.read_csv(filename)
    app = render_app(df)
    app.run_server()


if __name__ == "__main__":
    # Timer(1, open_browser).start()
    fire.Fire(main)
