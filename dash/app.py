"""
Define app along with its main components

Note:
    Although one could prefer using app within an overriding class, this
    practice is not recommended by a core writer of the Dash user guide.
    cf. @chriddyp: https://community.plotly.com/t/putting-a-dash-instance-inside-a-class/6097
"""
import dash
import dash_html_components as html

from filters import menu_graphs, menu_data
from sections import (
    section_header, section_graphs, section_data, section_metrics,
    section_footer,
)
from callbacks import add_chart_series_callback, add_metrics_callback


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

            menu_graphs(data),
            section_graphs(data, labels),

            menu_data('run_id', '0'),
            section_data('runs'),

            menu_data('experiment_id', '3a202149-8be2-408c-a3d8-baeae2de2987'),
            section_data('experiment'),

            section_metrics(data),

            *section_footer(),
        ],
    )


def build_callbacks(app, data, filters, labels):
    """ Define callbacks to update graphs and metrics on user event """
    add_chart_series_callback(app, data, filters, labels)
    add_metrics_callback(app)
