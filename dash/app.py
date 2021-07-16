"""
Define app along with its main components

Note:
    Although one could prefer using app within an overriding class, this
    practice is not recommended by a core writer of the Dash user guide.
    cf. @chriddyp: https://community.plotly.com/t/putting-a-dash-instance-inside-a-class/6097
"""
import dash
import dash_html_components as html

from filters import menu_filters
from sections import section_header, section_body
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
            section_header(),
            menu_filters(data),
            section_body(data, labels),
        ],
    )


def build_callbacks(app, data, filters, labels):
    """ Define callbacks to update graphs and metrics on user event """
    add_chart_series_callback(app, data, filters, labels)
