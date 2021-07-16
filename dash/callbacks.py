from dash.dependencies import Output, Input

from filters import filter_data, filter_week
from charts import line_chart
from fcts import outputs_graphs, inputs_menu
"""
Define callbacks to update Dash graphs and metrics on user event
"""
def add_chart_series_callback(app, data, filters, labels):
    """ Add standard automated Series charts based on user LABELS settings """
    # Define user events triggers
    inputs, names, signs = inputs_menu(filters)
    outputs = outputs_graphs(labels)

    @app.callback(outputs, inputs)
    def _update_series_charts(*inputs):
        """ Update all graphs similarly based on user choices """
        filtered_data = filter_data(data, inputs, names, signs)
        charts = [line_chart(filtered_data, l['x'], l['y']) for l in labels]
        return charts

    @app.callback(Output('graph-with-slider', 'figure'),
                  Input('week-slider', 'value'))
    def _update_figure(selected_week):
        filtered_data = filter_week(data, 'timestamp', selected_week)
        chart = line_chart(filtered_data, "timestamp", "energy_consumed")
        return chart
