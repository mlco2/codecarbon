from datetime import datetime as dt
from datetime import timedelta
from enum import unique

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from humanfriendly import format_timespan
from plotly.subplots import make_subplots

import dash
from dash.dependencies import Input, Output


def day_period(hour):
    """Get the day period given an hour"""
    if hour >= 0 and hour < 6:
        period = "Night"
    if hour >= 6 and hour < 12:
        period = "Morning"
    if hour >= 12 and hour < 18:
        period = "Afternoon"
    if hour >= 18 and hour <= 24:
        period = "Evening"
    if hour < 0 or hour > 24:
        raise ValueError(f"Hour should be within [0, 24], but is {hour}")
    return period


def force_date_format(date):
    return pd.to_datetime(date).date().isoformat()


def get_fig_co2_energy(energies, emissions, timestamps):
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

    return fig_co2_energy


def get_fig_energy_by_day_period(df):
    """Build a drawing for energy consumption along day periods"""
    df["period"] = get_period_of_the_day(df["timestamp"])
    fig_conso_energy_period = px.bar(
        df,
        x="period",
        y="energy_consumed",
        color="period",
        color_discrete_sequence=["#D95F02", "#764E9F"],
    )
    return fig_conso_energy_period


def get_period_of_the_day(timestamps):
    """Get day periods given a series of time"""
    # Extract hours
    hours = timestamps.apply(lambda d: d.hour)
    # Get corresponding day period
    day_periods = hours.apply(day_period)
    return day_periods


def get_unique_weeks(timestamps):
    """Get unique weeks from a series of timestamps"""
    unique_weeks = timestamps.apply(lambda dt: dt.week).unique()
    unique_weeks.sort()
    return unique_weeks


def load_data():
    return pd.read_csv("api_extract.csv", parse_dates=["timestamp"])


# ===== ===== ===== ======
# ===== Prepare data =====
# ===== ===== ===== ======

df = load_data()
weeks = get_unique_weeks(df["timestamp"])  # Here only: 23, 24

# Plot energy and emissions along time
fig_co2_energy = get_fig_co2_energy(
    df["energy_consumed"], df["emissions"], df["timestamp"]
)

# Plot conso_energy along periods of the day
fig_energy_period = get_fig_energy_by_day_period(df)


# ===== ===== ===== ======
# ===== Dash app layout ==
# ===== ===== ===== ======

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        # ======================= Banner =======================
        html.Img(
            src="https://raw.githubusercontent.com/mlco2/codecarbon/master/docs/edit/images/banner.png",
            alt="codecarbon logo",
        ),
        html.Br(),
        # ======================= Graph 1 =======================
        html.H1("Energy Consumed"),
        html.Br(),
        html.Label(
            ["Select Date:    "], style={"font-weight": "bold", "text-align": "center"}
        ),
        html.Br(),
        dcc.DatePickerRange(
            id="selected_date",
            calendar_orientation="horizontal",
            day_size=30,
            # end_date_placeholder_text='End Date',
            with_portal=False,
            first_day_of_week=0,
            reopen_calendar_on_clear=True,
            is_RTL=False,
            clearable=True,
            number_of_months_shown=1,
            min_date_allowed=dt(2020, 10, 1),
            max_date_allowed=pd.to_datetime("today").date(),
            initial_visible_month=dt(dt.today().year, dt.today().month, 1)
            .date()
            .isoformat(),
            start_date=(dt.today() - timedelta(days=60)).date().isoformat(),
            end_date=pd.to_datetime("today").date(),
            display_format="DD-MMM-YYYY",
            minimum_nights=0,
            persistence=True,
            persisted_props=["start_date"],
            persistence_type="memory",
            updatemode="singledate",
            style={"width": "70%", "offset": 2},
        ),
        dcc.Graph(id="energy-by-day"),
        html.Br(),
        # ======================= Graph 2 =======================
        html.H1("Energy Consumed"),
        dcc.Graph(id="graph-with-slider"),
        dcc.Slider(
            id="week-slider",
            min=weeks.min(),
            max=weeks.max(),
            value=weeks.min(),
            marks={str(week): str(week) for week in weeks},
            step=None,
        ),
        html.Br(),
        # ======================= Graph 3 =======================
        html.H1("Energy Consumed"),
        dcc.Graph(id="graph_conso_energy_period", figure=fig_energy_period),
        dcc.Graph(id="graph_co2_energy", figure=fig_co2_energy),
        html.Br(),
        # ======================= Metrics =======================
        html.H1("Other Information :"),
        html.H3("Total Energy Consumed :"),
        html.H3(f"{df['energy_consumed'].sum()} kWh"),
        html.H3("Total Emissions :"),
        html.H3(f"{df['emissions'].sum()} kg"),
        html.H3("Total duration :"),
        html.H3(format_timespan(df["duration"].sum())),
    ],
    style={"textAlign": "center"},
)


# ===== ===== ===== ======
# ===== Callback fcts ====
# ===== ===== ===== ======


@app.callback(
    Output("energy-by-day", "figure"),
    [Input("selected_date", "start_date"), Input("selected_date", "end_date")],
)
def update_figure(start_date, end_date):
    start_date = force_date_format(start_date)
    end_date = force_date_format(end_date)

    dff = df.rename(columns={"timestamp": "Date", "energy_consumed": "Energy Consumed"})
    dff = dff.reindex(index=dff.index[::-1])
    dff["Day"] = dff.Date.astype("str").str.split(" ").str.get(0)

    dff.set_index("Day", inplace=True)
    dff = dff.loc[start_date:end_date:]

    figg = go.Figure(go.Scatter(x=dff["Date"], y=dff["Energy Consumed"]))
    return figg


@app.callback(Output("graph-with-slider", "figure"), Input("week-slider", "value"))
def update_figure(selected_week):
    filtered_df = df[df["timestamp"].apply(lambda dt: dt.week) == selected_week]
    fig = px.scatter(filtered_df, x="timestamp", y="energy_consumed")
    fig.update_layout(transition_duration=500)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
