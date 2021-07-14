"""
Define layout sections: header, menu, body
"""
import dash_core_components as dcc
import dash_html_components as html


def header():
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


def body(labels):
    """ Composition of the layout page body """
    component = html.Div(
        children=[
            # Add a card automatically for each label defined in settings
            *[card_graph(label['y']) for label in labels],
        ],
        className="wrapper",
    )
    return component


def card_graph(identifier):
    """ Card composed of a single graph """
    component = html.Div(
        children=dcc.Graph(
            id=identifier,
            config={"displayModeBar": False},
        ),
        className="card",
    )
    return component
