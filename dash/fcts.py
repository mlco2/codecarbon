from dash.dependencies import Output, Input

def outputs_graphs(labels):
    return [Output(label['y'], 'figure') for label in labels]
