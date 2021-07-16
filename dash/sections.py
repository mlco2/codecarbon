"""
Define layout:
- sections: section_header and section_body
- subsections: subsection_metrics, subsection_timeseries, etc.
"""
import dash_core_components as dcc
import dash_html_components as html
from humanfriendly import format_timespan
from charts import fig_energy_by_day_period, fig_co2_energy


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


def section_body(data, labels):
    """
    Composition of the layout page body

    To add a section, add a function name (e.g. *metrics(data)):
    - The function should return one (or a list of) Dash components
    - When multiple components, prepend the function with a star to unwrap them
    """
    component = html.Div(
        children=[
            *subsection_timeseries(labels),
            card(subsection_metrics(data)),
            *subsection_static_graphs(data),
        ],
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


def subsection_metrics(data):
    """ General metrics on data """
    components = [
        html.H1('Other Information :'),
        html.H3('Total Energy Consumed :'),
        html.H3(f"{data['energy_consumed'].sum()} kWh"),
        html.H3('Total Emissions :'),
        html.H3(f"{data['emissions'].sum()} kg"),
        html.H3('Total duration :'),
        html.H3(format_timespan(data['duration'].sum())),
    ]
    return components


def subsection_timeseries(labels):
    """ Add a card automatically for each label defined in settings """
    return [card(graph(label['y'])) for label in labels]


def subsection_static_graphs(data):
    """ Add Bruna's Graphs """
    graphs = [
        html.H1('Energy Consumed'),
        graph('graph_conso_energy_period', fig_energy_by_day_period(data)),
        graph("graph_co2_energy", fig_co2_energy(data['energy_consumed'],
                                                 data['emissions'],
                                                 data['timestamp']))
    ]
    return graphs
