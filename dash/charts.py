"""
Graphs and charts and plots!
"""
import plotly.express as px
import plotly.graph_objects as go
from fcts import period_of_the_day
from plotly.subplots import make_subplots


def fig_co2_energy(energies, emissions, timestamps):
    """Build a drawing for energy consumption and CO2 emissions along time"""
    fig_co2_energy = make_subplots(rows=1, cols=2)

    fig_co2_energy.add_trace(
        go.Line(
            x=timestamps,
            y=energies,
            marker_color="goldenrod",
            name="Energy",
        ),
        row=1,
        col=1,
    )

    fig_co2_energy.add_trace(
        go.Line(
            x=timestamps,
            y=emissions,
            marker_color="#1B9E77",
            name="CO2",
        ),
        row=1,
        col=2,
    )

    fig_co2_energy.update_layout(title="Energy x CO2")
    fig_co2_energy.update_xaxes(showline=True, linewidth=2, gridcolor="#EDEDED")

    return fig_co2_energy


def fig_energy_by_day_period(data):
    """Build a drawing for energy consumption along day periods"""
    data["period"] = period_of_the_day(data["timestamp"])
    fig_conso_energy_period = px.bar(
        data,
        x="period",
        y="energy_consumed",
        color="period",
        color_discrete_sequence=["#D95F02", "#764E9F"],
        title="Energy consumption during the day",
    )
    return fig_conso_energy_period


def line_chart(data, x, y, text=None, transition=500):
    if not text:
        text = y

    chart = {
        "data": [
            {
                "x": data[x],
                "y": data[y],
                "type": "lines",
                "hovertemplate": "%{y:.5f}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": text,
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["#17B897"],
            "transition": {
                "duration": transition,
                "easing": "cubic-in-out",
            },
        },
    }
    return chart
