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
from fcts import outputs_graphs, inputs_menu
from settings import EXT_STYLESHEET, APP_TITLE, LABELS, FILTERS


# Load data
data = load_data()

# Instanciate Dash app
app = dash.Dash(__name__)
app.title = APP_TITLE
app.external_stylesheets=EXT_STYLESHEET

# Define page layout structure
app.layout = html.Div(
    children=[
        header(),
        menu_filters(data, FILTERS),
        body(LABELS),
    ],
)

# Define user events triggers
inputs, names, signs = inputs_menu(FILTERS)
outputs = outputs_graphs(LABELS)

@app.callback(outputs, inputs)
def update_charts(*inputs):
    """ Update all graphs similarly based on user choices """
    filtered_data = filter_data(data, inputs, names, signs)
    charts = [line_chart(filtered_data, labels['x'], labels['y'])
              for labels in LABELS]
    return charts



if __name__ == "__main__":
    app.run_server(debug=True)
