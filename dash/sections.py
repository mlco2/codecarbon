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
            # --------------- First card -----------------
            html.Div(
                # Only one graph for the card
                children=dcc.Graph(
                    id="emissions-chart",
                    config={"displayModeBar": False},
                ),
                className="card",
            ),

            # --------------- Second card -----------------
            html.Div(
                # Only one graph for the card
                children=dcc.Graph(
                    id="energy_consumed-chart",
                    config={"displayModeBar": False},
                ),
                className="card",
            ),
        ],
        className="wrapper",
    )
    return body
