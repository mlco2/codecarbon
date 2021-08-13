from charts import line_chart
from data_loader import load_experiment, load_runs
from fcts import inputs_menu, outputs_graphs, parse_input
from filters import filter_data, filter_week

from dash.dependencies import Input, Output

"""
Define callbacks to update Dash graphs and metrics on user event
"""


def add_chart_series_callback(app, data, filters, labels):
    """Add standard automated Series charts based on user LABELS settings"""
    # Define user events triggers
    inputs, names, signs = inputs_menu(filters)
    outputs = outputs_graphs(labels)

    @app.callback(outputs, inputs)
    def _update_series_charts(*inputs):
        """Update all graphs similarly based on user choices"""
        filtered_data = filter_data(data, inputs, names, signs)
        charts = [line_chart(filtered_data, l["x"], l["y"]) for l in labels]
        return charts

    @app.callback(Output("graph-with-slider", "figure"), Input("week-slider", "value"))
    def _update_figure(selected_week):
        filtered_data = filter_week(data, "timestamp", selected_week)
        chart = line_chart(filtered_data, "timestamp", "energy_consumed")
        return chart


def add_metrics_callback(app):
    @app.callback(
        Output(component_id="runs", component_property="children"),
        Input(component_id="run_id", component_property="value"),
    )
    def update_runs(input_value):
        runs_data = load_runs()
        parsed = parse_input(input_value)
        run = runs_data[parsed]
        return "Output: {}".format(run)

    @app.callback(
        Output(component_id="experiment", component_property="children"),
        Input(component_id="experiment_id", component_property="value"),
    )
    def update_experiment(input_value):
        try:
            experiment = load_experiment(input_value)
        except:
            experiment = load_experiment("3a202149-8be2-408c-a3d8-baeae2de2987")
        return "Output: {}".format(experiment)
