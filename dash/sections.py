"""
Define layout:
- sections: section_header and section_graphs
- subsections: section_metrics, subsection_timeseries, etc.
"""
import dash_core_components as dcc
import dash_html_components as html
from humanfriendly import format_timespan
from charts import fig_energy_by_day_period, fig_co2_energy
from fcts import unique_weeks


def card(component):
    """ Insert a component (or list of) into a shadowed card """
    card = html.Div(
        children=component,
        className="card",
    )
    return card


def graph(identifier, figure=None):
    """ Add a graph given its identifier """
    if figure:
        graph = dcc.Graph(
            id=identifier,
            figure=figure,
            config={"displayModeBar": False}
        )
    else:
        # A graph with callbacks
        graph = dcc.Graph(
            id=identifier,
            config={"displayModeBar": False}
        )
    return graph


def section_graphs(data, labels):
    """
    Composition of the layout page body

    To add a section, add a function name (e.g. *metrics(data)):
    - The function should return one (or a list of) Dash components
    - When multiple components, prepend the function with a star to unwrap them
    """
    component = html.Div(
        children=[
            *subsection_timeseries(labels),
            card(subsection_static_graphs(data)),
            card(subsection_slider(data)),
        ],
        className="wrapper",
    )
    return component

def section_data(id):
    component = html.Div(
        id=id,
        className="wrapper",
    )
    return component


def section_header():
    """ Composition and settings of the page header """
    component = html.Div(
            children=[
                html.H1(children="Evaluate CO2 Emissions",
                        className="header-title",
                ),
                html.P(children="Analyze CO2 emissions generated"
                                " using computer programs such as ML training",
                    className="header-description",
                ),
            ],
            className="header",
        )
    return component


def section_footer():
    return [html.Br() for i in range(5)]


def section_metrics(data):
    """ General metrics on data """
    div = html.Div(
        children = [
            html.H3('Metrics'),
            f"Total Energy Consumed : {round(data['energy_consumed'].sum(), 2)} kWh",
            html.Br(),
            f"Total Emissions : {round(data['emissions'].sum(), 2)} kg",
            html.Br(),
            f"Total duration : {format_timespan(data['duration'].sum())}",
            html.Br(),
        ],
        className='wrapper'
    )
    return div


def subsection_timeseries(labels):
    """ Add a card automatically for each label defined in settings """
    return [card(graph(label['y'])) for label in labels]


def subsection_static_graphs(data):
    """ Add static graphs """
    graphs = [
        graph('graph_conso_energy_period', fig_energy_by_day_period(data)),
        graph("graph_co2_energy", fig_co2_energy(data['energy_consumed'],
                                                 data['emissions'],
                                                 data['timestamp'])),
        html.Br(),
    ]
    return graphs


def subsection_slider(data):
    """ Add graph with slider """
    # Extract weeks from data
    weeks = unique_weeks(data['timestamp'])
    min_week = weeks.min()
    max_week = weeks.max()

    components = [
        dcc.Graph(id='graph-with-slider'),
        dcc.Slider(id='week-slider',
                   min=min_week,
                   max=max_week,
                   value=min_week,
                   marks={str(week): str(week) for week in weeks},
                   step=None),
    ]
    return components
