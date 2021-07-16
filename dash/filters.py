from functools import reduce
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
from fcts import get_first_elem

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
                id=f"{col_name}-filter",
                min_date_allowed=data[col_name].min().date(),
                max_date_allowed=data[col_name].max().date(),
                start_date=data[col_name].min().date(),
                end_date=data[col_name].max().date(),
            ),
        ],
    )
    return f_date


def filter_dropdown(data, col_name, type_='value', text=None, default_val='first'):
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
                options=[{"label": vec, type_: vec}
                         for vec in np.sort(data[col_name].unique())],
                clearable=False,
                className="dropdown",
                value=default_val,
            ),
        ],
    )
    return f_vec


def filter_week(data, date_field, selected_week):
    """ Filter data given a selected week """
    mask = data[date_field].apply(lambda dt: dt.week) == selected_week
    return data[mask]


def menu_filters(data):
    """
    Generate a menu with filtering components (dropdwons, date ranges, etc.)

    Note: Elements are not added automatically with new FILTERS in settings
          since it almost surely breaks the layout design and should be treated
          along with the css.
    """
    filters = html.Div(
        children=[
            filter_dropdown(data, col_name='run_id', type_='value', text='Run ID'),
            filter_dropdown(data, col_name='emissions', type_='value'),
            filter_date(data, col_name='timestamp'),
        ],
        className="menu",
    )
    return filters
