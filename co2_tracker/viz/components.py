import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import pandas as pd
import plotly.express as px


class Components:
    @staticmethod
    def get_header():
        return dbc.Jumbotron(
            [html.H1("Carbon Emissions", style={"textAlign": "center"})]
        )

    @staticmethod
    def get_net_summary():
        return html.Div(
            [
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
            style={"paddingLeft": 16, "paddingRight": 16},
        )

    @staticmethod
    def get_project_details():
        return html.Div(
            [
                html.Br(),
                html.Div(
                    [
                        html.H4(
                            [
                                "Infrastructure Hosted at ",
                                html.Strong(
                                    id="project_infrastructure_location",
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
                                        "paddingLeft": 10,
                                    },
                                ),
                            ],
                            style={"textAlign": "left", "float": "left"},
                        )
                    ]
                ),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                html.Div(
                    [
                        html.H2(
                            "Real World Equivalents", style={"textAlign": "center"}
                        ),
                        html.P(
                            [
                                html.Img(
                                    id="house_icon",
                                    style={
                                        "height": "10%",
                                        "width": "10%",
                                        "align": "right",
                                    },
                                ),
                                html.Img(
                                    id="car_icon",
                                    style={
                                        "height": "10%",
                                        "width": "10%",
                                        "align": "left",
                                    },
                                ),
                                html.Img(
                                    id="tv_icon",
                                    style={
                                        "height": "10%",
                                        "width": "10%",
                                        "align": "center",
                                    },
                                ),
                            ],
                            style={"marginLeft": "100px"},
                        ),
                    ],
                    style={"display": "inline-block"},
                ),
            ],
            style={"paddingLeft": 16, "paddingRight": 16},
        )

    @staticmethod
    def get_project_dropdown(df: pd.DataFrame):
        projects = sorted(list(df["project_name"].unique()))
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.H5(
                        "Select a Project",
                        style={"textAlign": "left", "fontWeight": "bold"},
                    ),
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
                        style={"textAlign": "center"},
                    ),
                    dcc.Graph(id="cloud_emissions_barchart"),
                ],
                id="cloud_emissions_barchart_component",
            )
        )

    @staticmethod
    def get_cloud_emissions_barchart_figure(cloud_emissions_barchart_data):
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
                color_continuous_scale=[
                    "rgb(0, 68, 27)",
                    "rgb(0, 109, 44)",
                    "rgb(35, 139, 69)",
                    "rgb(65, 171, 93)",
                    "rgb(116, 196, 118)",
                    "rgb(161, 217, 155)",
                    "rgb(199, 233, 192)",
                    "rgb(229, 245, 224)",
                    "rgb(189, 189, 189)",
                    "rgb(150, 150, 150)",
                ],  # px.colors.sequential.Greens_r,
                height=500,
            )
            .update_xaxes(tickangle=45)
            .update_layout(plot_bgcolor="rgb(255,255,255)")
        )

    @staticmethod
    def get_global_emissions_choropleth():
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.Br(),
                    html.H2(
                        "Global Emissions Equivalent", style={"textAlign": "center"}
                    ),
                    dcc.Graph(
                        id="global_emissions_choropleth", style={"paddingLeft": 200}
                    ),
                ]
            )
        )

    @staticmethod
    def get_global_emissions_choropleth_figure(choropleth_data):
        return px.choropleth(
            data_frame=choropleth_data,
            locations="iso_code",
            color="emissions",
            hover_data=["country", "emissions"],
            labels={
                "country": "Country",
                "emissions": "Carbon Equivalent (kg)",
                "iso_code": "Country Code",
            },
            color_continuous_scale=[
                "rgb(0, 68, 27)",
                "rgb(0, 109, 44)",
                "rgb(35, 139, 69)",
                "rgb(65, 171, 93)",
                "rgb(116, 196, 118)",
                "rgb(161, 217, 155)",
                "rgb(199, 233, 192)",
                "rgb(229, 245, 224)",
                "rgb(189, 189, 189)",
                "rgb(150, 150, 150)",
            ],  # px.colors.sequential.Greens_r,
        )

    @staticmethod
    def get_project_time_series():
        return html.Div(
            dbc.Col(
                [
                    html.Br(),
                    html.Br(),
                    html.H2("Emissions Timeline", style={"textAlign": "center"}),
                    dcc.Graph(id="project_time_series"),
                ]
            )
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
