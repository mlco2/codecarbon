from functools import reduce
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from fcts import get_first_elem, build_id

# def filter_data(data, run_id, start_date, end_date):
def filter_data(data, inputs, names, signs):
    """ Filter data based on user choices """
    masks = []
    for name, input, sign in zip(names, inputs, signs):
        if sign == '==':
            masks.append(data[name] == input)
        if sign == '>':
            masks.append(data[name] > input)
        if sign == '<':
            masks.append(data[name] < input)
        if sign == '>=':
            masks.append(data[name] >= input)
        if sign == '<=':
            masks.append(data[name] <= input)

    masks = reduce(np.logical_and, masks)
    data_filtered = data.loc[masks, :]

    return data_filtered


def filter_date(data, col_name, text='Date Range'):
    """ Filter a date vector and yield a calendar button """
    f_date = html.Div(
        children=[
            html.Div(
                children=text,
                className="menu-title"
                ),
            dcc.DatePickerRange(
                id="timestamp-filter",
                min_date_allowed=data[col_name].min().date(),
                max_date_allowed=data[col_name].max().date(),
                start_date=data[col_name].min().date(),
                end_date=data[col_name].max().date(),
            ),
        ],
    )
    return f_date


def filter_dropdown(data, col_name, type, text=None, default_val='first'):
    """
    Define a dropdown button for the provided column

    Args:
        default_val:
            first: graphs/metrics displayed using first vector value
            None: graphs/metrics not displayed until user selection
    """
    if not text:
        text = col_name

    if default_val == 'first':
        default_val = get_first_elem(data[col_name])

    f_vec = html.Div(
        children=[
            html.Div(
                children=text,
                className="menu-title"
            ),

            dcc.Dropdown(
                id = f"{col_name}-filter",
                options=[
                    {"label": vec, "value": vec}
                    for vec in np.sort(data[col_name].unique())
                ],
                clearable=False,
                className="dropdown",
                value=default_val,
            ),
        ],
    )
    return f_vec


def menu_filters(data, FILTERS):
    filters = html.Div(
        children=[
            filter_dropdown(data, col_name='run_id', type='value', text='Run ID'),
            filter_dropdown(data, col_name='duration', type='value'),
            filter_date(data, col_name='timestamp'),
        ],
        className="menu",
    )
    return filters
