import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd


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

    @staticmethod
    def get_hidden_project_data():
        return html.Div(id="hidden_project_data")  # , style={"display": "none"})

    @staticmethod
    def get_hidden_project_summary():
        return html.H1(
            dcc.Store(id="hidden_project_summary")
        )  # , style={"display": "none"})

    @staticmethod
    def get_project_summary(project_df: pd.DataFrame):
        last_run = project_df.iloc[-1]
        print(last_run)
        project_summary = {
            "last_run": {
                "timestamp": last_run.timestamp,
                "duration": last_run.duration,
                "emissions": last_run.emissions,
                "energy_consumed": last_run.energy_consumed,
            },
            "total": {
                "duration": sum(project_df.duration),
                "emissions": sum(project_df.emissions),
                "energy_consumed": sum(project_df.energy_consumed),
            },
            "country": last_run.country,
            "region": last_run.region,
            "on_cloud": last_run.on_cloud,
            "cloud_provider": last_run.cloud_provider,
            "cloud_region": last_run.cloud_region,
        }
        print(project_summary)
        return project_summary
