import numpy as np
import pandas as pd
from turtle import xcor
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
from sections import header, body
from charts import build_emission_chart, build_consumed_chart
from filters import filter_data, menu_filters
from settings import EXT_STYLESHEET, APP_TITLE
from data_loader import load_data


data = load_data()

app = dash.Dash(__name__, external_stylesheets=EXT_STYLESHEET)
app.title = APP_TITLE
app.layout = html.Div(
    children=[
        header(),
        menu_filters(data),
        body(),
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
    charts = []
    filtered_data = filter_data(data, run_id, start_date, end_date)
    charts.append(build_emission_chart(filtered_data))
    charts.append(build_consumed_chart(filtered_data))
    return charts


if __name__ == "__main__":
    app.run_server(debug=True)
