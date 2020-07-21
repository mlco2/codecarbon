from plotly.subplots import make_subplots
import plotly.graph_objects as go

import evaluate


def bar_chart_data(comparison_values, location, emissions):
    comparison_values.append([location, emissions])
    comparison_values.sort(key = lambda x: x[1])
    # bar chart colors
    colors = ['rgb(166, 189, 219)',] * len(comparison_values)
    labels = []
    data = []
    count = 0
    for pair in comparison_values:
        if pair[0] == location:
            colors[count] = 'rgb(28, 144, 153)'
        labels.append(pair[0])
        data.append(pair[1])
        count += 1
    return labels, data, colors


def default_comparison_graphs(kwh, location, emissions, intl_mix, us_data):
    comparison_data = evaluate.get_comparison_data(kwh, intl_mix, us_data, default_location=True)
    individual_chart_data = [comparison_data[6:], comparison_data[3:6], comparison_data[:3]]
    trace_names = ["Europe", "Global", "United States"]
    fig = make_subplots(rows=1, cols=3)

    for chart_col in range(3):
        comparison_values = individual_chart_data[chart_col]
        labels, data, colors = bar_chart_data(comparison_values, location, emissions)
        fig.add_trace(
            go.Bar(
                x=labels,
                y=data,
                marker_color=colors,
                marker_line_color='rgb(8,48,107)',
                marker_line_width=1.5,
                name = trace_names[chart_col-1],
                showlegend=False
            ),
            row=1,
            col=chart_col+1
        )

    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="United States",
        yaxis_title="CO2 (kg)",

        xaxis2_tickangle=-45,
        xaxis2_title="Europe",

        xaxis3_tickangle=-45,
        xaxis3_title="Global (excluding Europe and US)",
    )
    return fig


def custom_comparison_graph(kwh, location, emissions, locations, intl_mix, us_data):
    comparison_data = evaluate.get_comparison_data(kwh, intl_mix, us_data, locations)
    labels, data, colors = bar_chart_data(comparison_data, location, emissions)

    fig = go.Figure(
        data = go.Bar(
            x=labels,
            y=data,
            marker_color=colors,
            marker_line_color='rgb(8,48,107)',
            marker_line_width=1.5,
            showlegend=False
        )
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="Other Location",
        yaxis_title="CO2 (kg)",
    )
    return fig


def energy_mix_graph(location, intl_mix, us_mix):
    mix_data = evaluate.energy_mix(location, intl_mix, us_mix)
    labels = []
    values = []
    for pair in mix_data:
        labels.append(pair[0])
        values.append(pair[1])

    colors = ['rgb(202,0,32)', 'rgb(145,197,222)', 'rgb(244,165,130)', 'rgb(5,113,176)']

    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_traces(hoverinfo='label+percent', textinfo='percent+label', textfont_size=15,
                  marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    fig.update_layout(title_text="Energy Mix Data")
    return fig
