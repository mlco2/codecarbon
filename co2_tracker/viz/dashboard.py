import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import fire
import pandas as pd


def get_header():
    header = dbc.Jumbotron(
        [
            html.H1(
                "Carbon Emissions", className="display-6", style={"textAlign": "center"}
            )
        ]
    )
    return header


def get_project_dropdown(df: pd.DataFrame):
    projects = sorted(list(df["project_name"].unique()))
    return dbc.DropdownMenu(
        id="project",
        label="Project",
        children=[dbc.DropdownMenuItem(project) for project in projects],
        direction="up",
    )


def get_app(df: pd.DataFrame):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
    header = get_header()
    project_dropdown = get_project_dropdown(df)
    app.layout = dbc.Container(
        [header, project_dropdown], style={"padding-top": "50px"}
    )
    return app


def main(filename: str, port: int = 8050, debug: bool = False) -> None:
    df = pd.read_csv(filename)
    app = get_app(df)
    app.run_server(port=port, debug=debug)


if __name__ == "__main__":
    # Timer(1, open_browser).start()
    fire.Fire(main)
