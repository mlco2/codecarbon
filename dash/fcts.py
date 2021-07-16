from dash.dependencies import Output, Input

def build_id(d, sup):
    """ Append particule to build unique identifier """
    if sup == 'filter':
        id = f"{d['column']}-{sup}"
    if sup == 'graph':
        id = f"{d['y']}-{sup}"
    return id


def day_period(hour):
    """ Get the day period given an hour """
    if hour >= 0 and hour < 6:
        period = 'Night'
    if hour >= 6 and hour < 12:
        period = 'Morning'
    if hour >= 12 and hour < 18:
        period = 'Afternoon'
    if hour >= 18 and hour <= 24:
        period = 'Evening'
    if hour < 0 or hour > 24:
        raise ValueError(f"Hour should be within [0, 24], but is {hour}")
    return period


def get_first_elem(s):
    """ Get first alpha-numerical element of a Pandas Series """
    return s.sort_values().iloc[0]


def period_of_the_day(timestamps):
    """ Get day periods given a series of time """
    hours = timestamps.apply(lambda d: d.hour)
    day_periods = hours.apply(day_period)
    return day_periods


def inputs_menu(filters):
    """ Build input buttons """
    inputs = []
    names = []
    signs = []
    for filt in filters:
        id = build_id(filt, sup='filter')

        if filt['button_type'] == 'dropdown':
            inputs.append(Input(id, 'value'))
            names.append(filt['column'])
            signs.append(filt['sign'])

        if filt['button_type'] == 'date-range':
            inputs.append(Input(id, "start_date"))
            inputs.append(Input(id, "end_date"))
            names.append(filt['column'])
            signs.append('>')
            signs.append('<')

    return inputs, names, signs


def outputs_graphs(labels):
    outputs = []
    for label in labels:
        id = build_id(label, sup='graph')
        outputs.append(Output(label['y'], 'figure'))
    return outputs


def unique_weeks(timestamps):
    """ Extract unique weeks from a series of timestamps """
    unique_weeks = timestamps.apply(lambda dt: dt.week).unique()
    unique_weeks.sort()
    return unique_weeks
