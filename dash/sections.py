import dash_core_components as dcc
import dash_html_components as html

def header():
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


def body():
    body = html.Div(
        children=[
            card_graph(id="emissions-chart"),
            card_graph(id="energy_consumed-chart"),
        ],
        className="wrapper",
    )
    return body


def card_graph(id):
    card = html.Div(
        children=dcc.Graph(
            id=id,
            config={"displayModeBar": False},
        ),
        className="card",
    )
    return card
