from datetime import date
import dash_bootstrap_components as dbc
from dash import dcc, html


class Components:
    @staticmethod
    def get_header():
        return dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "WARNING : This is an alpha preview version released for Earth Day 2022. Some metrics are not accurate."
                                )
                            ],
                            className="inner",
                        )
                    ],
                    className="banner",
                ),
                html.A(
                    [html.Img(src="/assets/logo.png")], href="https://codecarbon.io"
                ),
                html.P("Track and reduce CO2 emissions from your computing"),
                dcc.DatePickerRange(
                    id="periode",
                    day_size=39,
                    month_format="MMMM Y",
                    end_date_placeholder_text="MMMM Y",
                    # should be calculated from today() like minus 1 week
                    start_date=date(2020, 1, 1),
                    min_date_allowed=date(2000, 1, 1),
                    max_date_allowed=date.today(),
                    initial_visible_month=date.today(),
                    end_date=date.today(),
                ),
            ],
            xs=12,
            sm=12,
            md=12,
            lg=5,
            xl=5,
        )

    def get_global_summary(self):
        return dbc.Col(
            [
                html.H5("Global"),
                dbc.CardGroup(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Energy consumed",
                                            className="text-center",
                                        ),
                                        html.H3(
                                            id="Tot_Energy_Consumed",
                                            className="text-center",
                                        ),
                                        html.P("kWh", className="text-center"),
                                    ]
                                )
                            ],
                        ),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Emissions produced",
                                            className="text-center",
                                        ),
                                        html.H4(
                                            id="Tot_Emissions",
                                            className="text-center",
                                        ),
                                        html.P(
                                            "Kg. Eq. CO2",
                                            className="text-center",
                                        ),
                                    ]
                                )
                            ],
                        ),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Cumulative duration",
                                            className="text-center",
                                        ),
                                        html.H4(
                                            id="Tot_Duration",
                                            className="text-center",
                                        ),
                                        html.P(
                                            id="Tot_Duration_unit",
                                            className="text-center",
                                        ),
                                    ]
                                )
                            ],
                        ),
                    ],
                    className="shadow",
                ),
            ]
        )

    def get_household_equivalent(self):
        return dbc.Card(
            [
                dbc.CardImg(
                    src="/assets/house_icon.png",
                    className="align-self-center",
                ),
                dbc.CardBody(
                    [
                        html.H4(
                            id="houseHold",
                        ),
                        html.P(
                            "of an american household weekly energy consumption",
                            className="card-title",
                        ),
                    ]
                ),
            ],
        )

    def get_car_equivalent(self):
        return dbc.Card(
            [
                dbc.CardImg(
                    src="/assets/car_icon.png",  # app.get_asset_url("car_icon.png"), #
                    className="align-self-center",
                ),
                dbc.CardBody(
                    [
                        html.H4(
                            id="car",
                        ),
                        html.P(
                            "miles driven",
                            className="card-title",
                        ),
                    ]
                ),
            ],
        )

    def get_tv_equivalent(self):
        return dbc.Card(
            [
                dbc.CardImg(
                    src="/assets/tv_icon.png",
                    className="align-self-center",
                ),
                dbc.CardBody(
                    [
                        html.H4(
                            id="tv",
                        ),
                        html.P(
                            "of TV",
                            className="card-title",
                        ),
                    ]
                ),
            ],
        )
