from dash.dependencies import Output, Input

def build_id(d, sup):
    """ Append particule to build unique identifier """
    if sup == 'filter':
        id = f"{d['column']}-{sup}"
    if sup == 'graph':
        id = f"{d['y']}-{sup}"
    return id


def get_first_elem(s):
    """ Get first alpha-numerical element of a Pandas Series """
    return s.sort_values().iloc[0]


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
