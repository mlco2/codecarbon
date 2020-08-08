from plotly.subplots import make_subplots
import plotly.graph_objects as go

import evaluate


def bar_chart_data(comparison_values, location, emissions):
    comparison_values.append([location, emissions])
    comparison_values.sort(key=lambda x: x[1])
    # update bar chart colors
    colors = ["rgb(166, 189, 219)"] * len(comparison_values)
    labels = []
    data = []
    count = 0
    for pair in comparison_values:
        if pair[0] == location:
            colors[count] = "rgb(28, 144, 153)"
        labels.append(pair[0])
        data.append(pair[1])
        count += 1
    return labels, data, colors


def default_comparison_graphs(kwh, location, emissions):
    comparison_data = evaluate.get_comparison_data(kwh, default_location=True)
    individual_chart_data = [
        comparison_data[6:],
        comparison_data[3:6],
        comparison_data[:3],
    ]
    trace_names = ["Europe", "Global", "United States"]
    fig = make_subplots(rows=1, cols=3)

    for chart_col in range(3):
        comparison_values = individual_chart_data[chart_col]
        labels, data, colors = bar_chart_data(comparison_values, location, emissions)
        label_text = [round(i, 2) for i in data]
        fig.add_trace(
            go.Bar(
                x=labels,
                y=data,
                text=label_text,
                textposition="outside",
                marker_color=colors,
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                name=trace_names[chart_col - 1],
                showlegend=False,
            ),
            row=1,
            col=chart_col + 1,
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
    emissions_list = [value[1] for value in comparison_values]
    fig.update_yaxes(range=(0, 1.1 * emissions_list[-1]))
    return fig


def custom_comparison_graph(kwh, location, emissions, locations):
    comparison_data = evaluate.get_comparison_data(kwh, locations)
    labels, data, colors = bar_chart_data(comparison_data, location, emissions)
    label_text = [round(value, 2) for value in data]

    fig = go.Figure(
        data=go.Bar(
            x=labels,
            y=data,
            text=label_text,
            textposition="outside",
            marker_color=colors,
            marker_line_color="rgb(8,48,107)",
            marker_line_width=1.5,
            showlegend=False,
        )
    )
    fig.update_layout(
        xaxis_tickangle=-45, xaxis_title="Location", yaxis_title="CO2 (kg)"
    )
    emissions_list = [value[1] for value in comparison_data]
    fig.update_yaxes(range=(0, 1.1 * emissions_list[-1]))
    return fig


def energy_mix_data(location, countries_with_regional_energy_mix):
    mix_data = evaluate.energy_mix(location)
    labels = []
    values = []
    for pair in mix_data:
        labels.append(pair[0])
        values.append(pair[1])
    return labels, values


def energy_mix_graph(location, countries_with_regional_energy_mix):
    labels, values = energy_mix_data(location, countries_with_regional_energy_mix)

    colors = ["rgb(202,0,32)", "rgb(145,197,222)", "rgb(244,165,130)", "rgb(5,113,176)"]
    title = "Energy Mix: " + location

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                showlegend=False,
                insidetextorientation="horizontal",
            )
        ]
    )
    fig.update_traces(
        hoverinfo="label+percent",
        textinfo="percent+label",
        textfont_size=15,
        marker=dict(colors=colors, line=dict(color="#000000", width=2)),
    )
    fig.update_layout(margin=dict(t=60, b=60, l=60, r=60))
    return fig
