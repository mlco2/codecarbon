import numpy as np
import pandas as pd
from turtle import xcor

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

from sections import header, body
from charts import line_chart
from filters import filter_data, menu_filters
from data_loader import load_data
from fcts import outputs_graphs
from settings import EXT_STYLESHEET, APP_TITLE, LABELS

data = load_data()

app = dash.Dash(__name__)
app.title = APP_TITLE
app.external_stylesheets=EXT_STYLESHEET

app.layout = html.Div(
    children=[
        header(),
        menu_filters(data),
        body(LABELS),
    ],
)

@app.callback(
    [
        *outputs_graphs(LABELS)
    ],
    [
        Input("run_id-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(run_id, start_date, end_date):
    """ Update all graphs similarly based on user choices """
    filtered_data = filter_data(data, run_id, start_date, end_date)
    charts = [line_chart(filtered_data, pair['x'], pair['y']) for pair in LABELS]
    return charts


if __name__ == "__main__":
    app.run_server(debug=True)
