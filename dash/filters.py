import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html

def filter_data(data, run_id, start_date, end_date):
    """ Filter data based on user choices """
    mask = (
        (data['run_id'] == run_id)
        & (data['timestamp'] >= start_date)
        & (data['timestamp'] <= end_date)
    )
    return data.loc[mask, :]


def menu_filters(data):
    filters = html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        children="Run ID",
                        className="menu-title"
                    ),

                    dcc.Dropdown(
                        id="run_id-filter",
                        options=[
                            {"label": run_id, "value": run_id}
                            for run_id in np.sort(data['run_id'].unique())
                        ],
                        clearable=False,
                        className="dropdown",
                    ),
                ],
            ),

            html.Div(
                children=[
                    html.Div(
                        children="Date Range",
                        className="menu-title"
                        ),
                    dcc.DatePickerRange(
                        id="date-range",
                        min_date_allowed=data['timestamp'].min().date(),
                        max_date_allowed=data['timestamp'].max().date(),
                        start_date=data['timestamp'].min().date(),
                        end_date=data['timestamp'].max().date(),
                    ),
                ],
            ),
        ],
        className="menu",
    )
    return filters
