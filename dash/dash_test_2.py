from turtle import xcor
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import numpy as np
import pandas as pd
from components import header, EXT_STYLESHEET

data = pd.read_csv('api_extract.csv', parse_dates=['timestamp'])

app = dash.Dash(__name__, external_stylesheets=EXT_STYLESHEET)
app.title = "CodeCarbon Measure ML CO2 Emissions"
app.layout = html.Div(
    children=[
        header(),

        # ========== Interactive select ===========

        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            children="Run ID",
                            className="menu-title"
                        ),

                        dcc.Dropdown(
                            id="run_id-filter",
                            options=[
                                {"label": run_id, "value": run_id}
                                for run_id in np.sort(data['run_id'].unique())
                            ],
                            value="731e791d-dd75-44a1-a253-b875bdc7ffbf",
                            clearable=False,
                            className="dropdown",
                        ),
                    ],
                ),

                html.Div(
                    children=[
                        html.Div(
                            children="Date Range",
                            className="menu-title"
                            ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data['timestamp'].min().date(),
                            max_date_allowed=data['timestamp'].max().date(),
                            start_date=data['timestamp'].min().date(),
                            end_date=data['timestamp'].max().date(),
                        ),
                    ],
                ),
            ],
            className="menu",
        ),


        # ========== BODY (wrapper) ===========
        html.Div(
            children=[
                # --------------- First card -----------------
                html.Div(
                    # Only one graph for the card
                    children=dcc.Graph(
                        id="emissions-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),

                # --------------- Second card -----------------
                html.Div(
                    # Only one graph for the card
                    children=dcc.Graph(
                        id="energy_consumed-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ],
)


@app.callback(
    [Output("emissions-chart", "figure"), Output("energy_consumed-chart", "figure")],
    [
        Input("run_id-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(run_id, start_date, end_date):
    mask = (
        (data['run_id'] == run_id)
        & (data['timestamp'] >= start_date)
        & (data['timestamp'] <= end_date)
    )
    filtered_data = data.loc[mask, :]

    emission_chart = {
        "data": [
            {
                "x": filtered_data["timestamp"],
                "y": filtered_data["emissions"],
                "type": "lines",
                "hovertemplate": "%{y:.5f}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Emissions",
                "x": .05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    energy_consumed_chart = {
        "data": [
            {
                "x": filtered_data["timestamp"],
                "y": filtered_data["energy_consumed"],
                "type": "lines",
                "hovertemplate": "$%{y:.2f}"
                                    "<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Energy consumed",
                "x": .05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["#17B897"],
        },

    }
    return emission_chart, energy_consumed_chart


if __name__ == "__main__":
    app.run_server(debug=True)
