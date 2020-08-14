import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px


class Components:
    @staticmethod
    def get_header():
        return dbc.Jumbotron(
            [
                html.H1(
                    "Carbon Emissions",
                    className="display-6",
                    style={"textAlign": "center"},
                )
            ]
        )

    @staticmethod
    def get_project_dropdown(df: pd.DataFrame):
        projects = sorted(list(df["project_name"].unique()))
        return dbc.Col(
            [
                html.H5(
                    "Select a Project",
                    style={"text-align": "left", "font-weight": "bold"},
                ),
                dcc.Dropdown(
                    id="project_name",
                    options=[{"label": i, "value": i} for i in projects],
                    value=projects[0],
                ),
            ],
            style={"display": "inline-block"},
        )

    @staticmethod
    def get_cloud_emissions_barchart():
        return dbc.Col(
            [
                html.Br(),
                html.H2(
                    [
                        "Emissions Across ",
                        html.Strong(
                            id="cloud_provider_name",
                            style={"font-weight": "normal", "color": "green"},
                        ),
                        " Regions",
                    ],
                    style={"text-align": "center"},
                ),
                dcc.Graph(id="cloud_emissions_barchart"),
            ],
            id="cloud_emissions_barchart_component",
            # style={"display": "block"},
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
                    "rgb(115, 115, 115)",
                ],  # px.colors.sequential.Greens_r,
                height=500,
            )
            .update_xaxes(tickangle=45)
            .update_layout(plot_bgcolor="rgb(255,255,255)")
        )

    @staticmethod
    def get_global_emissions_choropleth():
        return dbc.Col(
            [
                html.Br(),
                html.H2("Global Emissions Equivalent", style={"text-align": "center"}),
                dcc.Graph(id="global_emissions_choropleth"),
            ]
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
                "rgb(115, 115, 115)",
            ],  # px.colors.sequential.Greens_r,
        )

    @staticmethod
    def get_hidden_project_data():
        return html.Div(id="hidden_project_data")  # , style={"display": "none"})

    @staticmethod
    def get_hidden_project_summary():
        return html.H1(
            dcc.Store(id="hidden_project_summary")  # , style={"display": "none"}
        )
