import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import pandas as pd
import plotly.express as px


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
    def get_header():
        return dbc.Jumbotron(
            [
                html.H1("Carbon Footprint", style={"textAlign": "center"}),
                html.P(
                    "Track emissions from ML experiments",
                    style={"textAlign": "center"},
                    className="lead",
                ),
            ]
        )

    @staticmethod
    def get_net_summary():
        return html.Div(
            [
                html.H2("Across All Projects", style={"textAlign": "center"}),
                html.H4(
                    [
                        "Net Power Consumption : ",
                        html.Strong(
                            id="net_power_consumption",
                            style={"fontWeight": "normal", "color": "green"},
                        ),
                    ],
                    style={"textAlign": "left", "float": "left"},
                ),
                html.H4(
                    [
                        "Net Carbon Equivalent : ",
                        html.Strong(
                            id="net_carbon_equivalent",
                            style={"fontWeight": "normal", "color": "green"},
                        ),
                    ],
                    style={"textAlign": "right", "float": "right"},
                ),
            ],
            style={"paddingLeft": "1.4%", "paddingRight": "1.4%"},
        )

    @staticmethod
    def get_project_dropdown(df: pd.DataFrame):
        projects = sorted(list(df["project_name"].unique()))
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.H3("Select a Project", style={"textAlign": "left"}),
                    dcc.Dropdown(
                        id="project_name",
                        options=[{"label": i, "value": i} for i in projects],
                        value=projects[0],
                    ),
                ],
                style={"display": "inline-block"},
            )
        )

    @staticmethod
    def get_project_details():
        return html.Div(
            [
                html.Br(),
                html.Div(
                    [
                        html.H3(
                            [
                                "Infrastructure Hosted at ",
                                html.Strong(
                                    id="project_infrastructure_location",
                                    style={"fontWeight": "normal", "color": "green"},
                                ),
                            ],
                            style={"textAlign": "left", "float": "left"},
                        )
                    ]
                ),
                html.Br(),
                html.Br(),
                html.Div(
                    [
                        html.H4(
                            [
                                "Power Consumption Across All Experiments : ",
                                html.Strong(
                                    id="project_power_consumption",
                                    style={"fontWeight": "normal", "color": "green"},
                                ),
                            ],
                            style={"textAlign": "left", "float": "left"},
                        ),
                        html.H4(
                            [
                                "Last Run Power Consumption : ",
                                html.Strong(
                                    id="last_run_power_consumption",
                                    style={"fontWeight": "normal", "color": "green"},
                                ),
                            ],
                            style={"textAlign": "right", "float": "right"},
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        html.H4(
                            [
                                "Carbon Equivalent Across All Experiments : ",
                                html.Strong(
                                    id="project_carbon_equivalent",
                                    style={
                                        "textAlign": "right",
                                        "float": "right",
                                        "color": "green",
                                        "fontWeight": "bold",
                                        "paddingLeft": 5,
                                    },
                                ),
                            ],
                            style={"textAlign": "left", "float": "left"},
                        ),
                        html.H4(
                            [
                                "Last Run Carbon Equivalent : ",
                                html.Strong(
                                    id="last_run_carbon_equivalent",
                                    style={"fontWeight": "normal", "color": "green"},
                                ),
                            ],
                            style={"textAlign": "right", "float": "right"},
                        ),
                    ]
                ),
            ],
            style={"paddingLeft": "1.4%", "paddingRight": "1.4%"},
        )

    @staticmethod
    def get_exemplary_equivalents():
        return html.Div(
            [
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Div(
                    [
                        html.H2("Exemplary Equivalents", style={"textAlign": "center"}),
                        html.Br(),
                        html.P(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            id="house_icon",
                                            style={"height": "20%", "width": "50%"},
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    id="household_fraction",
                                                    style={
                                                        "color": "green",
                                                        "fontSize": 20,
                                                        "paddingLeft": "4%",
                                                    },
                                                ),
                                                html.H5(
                                                    "of weekly",
                                                    style={"paddingLeft": "3.5%"},
                                                ),
                                                html.H5(
                                                    "American",
                                                    style={"paddingLeft": "2.8%"},
                                                ),
                                                html.H5("household"),
                                                html.H5(
                                                    "emissions",
                                                    style={"paddingLeft": "1.4%"},
                                                ),
                                            ]
                                        ),
                                    ],
                                    style={"float": "left", "width": "25%"},
                                ),
                                html.Div(
                                    [
                                        html.Img(
                                            id="car_icon",
                                            style={
                                                "height": "45%",
                                                "width": "32.5%",
                                                "paddingLeft": "4%",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    id="car_miles",
                                                    style={
                                                        "color": "green",
                                                        "fontWeight": "bold",
                                                        "fontSize": 20,
                                                    },
                                                ),
                                                html.H5(
                                                    "driven",
                                                    style={"paddingLeft": "12%"},
                                                ),
                                            ]
                                        ),
                                    ],
                                    style={
                                        "float": "left",
                                        "width": "50%",
                                        "paddingLeft": 90,
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Img(
                                            id="tv_icon",
                                            style={
                                                "height": "35%",
                                                "width": "53%",
                                                "paddingLeft": "5%",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    id="tv_time",
                                                    style={
                                                        "color": "green",
                                                        "fontSize": 20,
                                                        "paddingLeft": "8%",
                                                    },
                                                ),
                                                html.H5(
                                                    "of 32-inch",
                                                    style={"paddingLeft": "4.8%"},
                                                ),
                                                html.H5(
                                                    "LCD TV",
                                                    style={"paddingLeft": "10%"},
                                                ),
                                                html.H5(
                                                    "watched",
                                                    style={"paddingLeft": "6.4%"},
                                                ),
                                            ]
                                        ),
                                    ],
                                    style={"float": "right", "width": "25%"},
                                ),
                            ],
                            style={"paddingLeft": "20%", "paddingRight": "15%"},
                        ),
                    ],
                    style={"display": "inline-block"},
                ),
            ]
        )

    @staticmethod
    def get_cloud_emissions_barchart():
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.Br(),
                    html.H2(
                        [
                            "Emissions Across ",
                            html.Strong(
                                id="cloud_provider_name",
                                style={"fontWeight": "normal", "color": "green"},
                            ),
                            " Regions",
                        ],
                        style={"textAlign": "center", "paddingLeft": "18%"},
                    ),
                    dcc.Graph(id="cloud_emissions_barchart"),
                ],
                id="cloud_emissions_barchart_component",
            ),
            style={"marginLeft": "-18%"},
        )

    def get_cloud_emissions_barchart_figure(self, cloud_emissions_barchart_data):
        return (
            px.bar(
                cloud_emissions_barchart_data,
                x="region",
                y="emissions",
                hover_data=["region", "country", "emissions"],
                color="emissions",
                labels={
                    "emissions": "Carbon Equivalent (kg)",
                    "region": "Region",
                    "country": "Country",
                },
                color_continuous_scale=self.colorscale,
                height=500,
                width=1500,
            )
            .update_xaxes(tickangle=45)
            .update_layout(plot_bgcolor="rgb(255,255,255)")
        )

    @staticmethod
    def get_global_comparison():
        return html.Div(
            [
                html.Br(),
                html.Br(),
                html.H2(
                    "Global Benchmarks",
                    style={
                        "textAlign": "center",
                        "paddingLeft": "15%",
                        "marginLeft": "-15%",
                    },
                ),
                html.Br(),
                html.Br(),
                dcc.Tabs(
                    id="global_benchmarks",
                    value="emissions_tab",
                    children=[
                        dcc.Tab(label="Emissions Equivalent", value="emissions_tab"),
                        dcc.Tab(label="Energy Mix", value="energy_mix_tab"),
                    ],
                ),
                html.Div(id="tab_content"),
            ]
        )

    def get_global_emissions_choropleth(self, figure):
        return html.Div(
            dbc.Col(dcc.Graph(id="global_emissions_choropleth", figure=figure)),
            style={"marginLeft": "-16%"},
        )

    def get_global_emissions_choropleth_figure(self, choropleth_data):
        return px.choropleth(
            data_frame=choropleth_data,
            locations="iso_code",
            color="emissions",
            hover_data=[
                "country",
                "emissions",
                "coal",
                "petroleum",
                "natural_gas",
                "low_carbon",
            ],
            labels={
                "country": "Country",
                "emissions": "Carbon Equivalent (kg)",
                "iso_code": "Country Code",
                "coal": "Coal Energy (%)",
                "petroleum": "Petroleum Energy (%)",
                "natural_gas": "Natural Gas Energy (%)",
                "low_carbon": "Low Carbon Energy (%)",
            },
            width=1400,
            height=600,
            color_continuous_scale=self.colorscale,
        )

    def get_global_energy_mix_choropleth(self, figure):
        return html.Div(
            dbc.Col(dcc.Graph(id="global_energy_mix_choropleth", figure=figure)),
            style={"marginLeft": "-16%"},
        )

    def get_global_energy_mix_choropleth_figure(self, choropleth_data):
        energy_type = "coal"
        return px.choropleth(
            data_frame=choropleth_data,
            locations="iso_code",
            color=energy_type,
            hover_data=[
                "country",
                "emissions",
                energy_type,
                "petroleum",
                "natural_gas",
                "low_carbon",
            ],
            labels={
                "country": "Country",
                "emissions": "Carbon Equivalent (kg)",
                "iso_code": "Country Code",
                energy_type: "Coal Energy (%)",
                # "petroleum": "Petroleum Energy (%)",
                # "natural_gas": "Natural Gas Energy (%)",
                # "low_carbon": "Low Carbon Energy (%)",
            },
            width=1400,
            height=600,
            color_continuous_scale=self.colorscale,
        )

    @staticmethod
    def get_project_time_series():
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.H2("Emissions Timeline", style={"textAlign": "center"}),
                    dcc.Graph(id="project_time_series"),
                ]
            ),
            style={"paddingLeft": "3%"},
        )

    @staticmethod
    def get_project_time_series_figure(project_data: dt.DataTable):
        return (
            px.line(
                project_data,
                x="timestamp",
                y="emissions",
                hover_data=["emissions"],
                labels={
                    "emissions": "Carbon Equivalent (kg)",
                    "timestamp": "Timestamp",
                },
            )
            .update_traces(line_color="green")
            .update_layout(plot_bgcolor="rgb(255,255,255)")
        )

    @staticmethod
    def get_hidden_project_data():
        return html.Div(id="hidden_project_data", style={"display": "none"})

    @staticmethod
    def get_hidden_project_summary():
        return html.Div(
            dcc.Store(id="hidden_project_summary"), style={"display": "none"}
        )
