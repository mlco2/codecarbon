import dash_core_components as dcc
import dash_html_components as html

def header():
    """ Composition and settings of the page header """
    h = html.Div(
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
    return h


def body(labels):
    """ Composition of the layout page body """
    body = html.Div(
        children=[
            *[card_graph(id=label['y']) for label in labels],
        ],
        className="wrapper",
    )
    return body


def card_graph(id):
    """ Card composed of a single graph """
    card = html.Div(
        children=dcc.Graph(
            id=id,
            config={"displayModeBar": False},
        ),
        className="card",
    )
    return card
