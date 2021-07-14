"""
Define app along with its main components
"""
import dash
import dash_html_components as html

from filters import menu_filters
from sections import header, body
from callbacks import add_chart_series_callback


def init_app(title, stylesheet):
    app = dash.Dash(__name__)
    app.title = title
    app.external_stylesheets = stylesheet
    return app


def build_layout(app, data, labels):
    """ Define layout sections and ordering """
    app.layout = html.Div(
        children=[
            header(),
            menu_filters(data),
            body(labels),
        ],
    )


def build_callbacks(app, data, filters, labels):
    """ Define callbacks to update graphs and metrics on user event """
    add_chart_series_callback(app, data, filters, labels)
