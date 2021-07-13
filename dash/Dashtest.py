import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
from datetime import datetime as dt, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from humanfriendly import format_timespan

df = pd.read_csv('api_extract.csv', parse_dates=['timestamp'])
df_api = pd.read_csv('api_extract.csv', parse_dates=['timestamp'])

weeks = df_api['timestamp'].apply(lambda dt: dt.week).unique()  # 23, 24
weeks.sort()


fig_co2_energy = make_subplots(rows=1, cols=2)


fig_co2_energy.add_trace(go.Line(x=df['timestamp'], y=df['energy_consumed'],
                         marker_color='goldenrod',
                         name='Energy'), row = 1, col=1)
fig_co2_energy.add_trace(go.Line(x=df['timestamp'], y=df['emissions'],
                         marker_color='#1B9E77',
                         name='CO2'
                         ), row= 1, col = 2)
fig_co2_energy.update_layout(
        title = 'Energy x CO2')

def get_period_of_the_day(a):
    x = a.timestamp.astype('str').str.split(' ').str.get(1)
    y = x.str.split(":").str.get(0)
    y = y.astype('int')
    l = []
    for i in y:
        if i >= 12 and i < 18:
            l.append('Afternoon')
        elif i >= 18 and i < 24:
            l.append('Evening')
        elif i >= 6 and i < 12:
            l.append('Morning')
        else:
            l.append('Night')
    return l

df['Period'] = get_period_of_the_day(df)

fig_conso_energy_period = px.bar(data_frame=df, x = 'Period', y = 'energy_consumed', color='Period',
                                 color_discrete_sequence=["#D95F02", "#764E9F"])



app = dash.Dash(__name__)

app.layout = html.Div([
    html.Img(src='https://raw.githubusercontent.com/mlco2/codecarbon/master/docs/edit/images/banner.png', alt='codecarbon logo'),
    html.Br(),
    html.H1("Energy Consumed"),

    html.Br(),

    html.Label(['Select Date:    '],style={'font-weight': 'bold', "text-align": "center"}),

    html.Br(),

    dcc.DatePickerRange(id = "selected_date", calendar_orientation='horizontal', day_size=30,
                            #end_date_placeholder_text='End Date',
                            with_portal=False, first_day_of_week=0, reopen_calendar_on_clear=True, is_RTL=False,
                            clearable=True, number_of_months_shown=1, min_date_allowed=dt(2020, 10, 1),max_date_allowed=pd.to_datetime("today").date(),
                            initial_visible_month= dt(dt.today().year, dt.today().month, 1).date().isoformat(),
                            start_date=(dt.today() - timedelta(days=1)).date().isoformat(), end_date=pd.to_datetime("today").date(),
                            display_format="DD-MMM-YYYY", minimum_nights=0,
                            persistence=True, persisted_props=["start_date"], persistence_type="memory",
                            updatemode="singledate", style={'width': '70%', 'offset': 2}),
    dcc.Graph(id='energy-by-day'),

    html.Br(),

    html.H1("Energy Consumed"),

    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        id='week-slider',
        min=weeks.min(),
        max=weeks.max(),
        value=weeks.min(),
        marks={str(week): str(week) for week in weeks},
        step=None
    ),
    html.Br(),

    html.H1('Energy Consumed'),

    dcc.Graph(id="graph_conso_energy_period", figure = fig_conso_energy_period),

    dcc.Graph(id="graph_co2_energy", figure=fig_co2_energy),

    html.Br(),

    html.H1('Other Information :'),

    html.H3('Total Energy Consumed :'),
    html.H3(f"{df['energy_consumed'].sum()} kWh"),
    html.H3('Total Emissions :'),
    html.H3(f"{df['emissions'].sum()} kg"),
    html.H3('Total duration :'),
    html.H3(format_timespan(df['duration'].sum())),

],style={'textAlign':'center'})

@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('week-slider', 'value'))
def update_figure(selected_week):
    filtered_df = df_api[df_api['timestamp'].apply(lambda dt: dt.week) == selected_week]
    fig = px.scatter(filtered_df, x="timestamp", y="energy_consumed")
    fig.update_layout(transition_duration=500)
    return fig


@app.callback(
    Output('energy-by-day', 'figure'),
    [Input(component_id='selected_date', component_property='start_date'),
     Input(component_id='selected_date', component_property='end_date')])
def update_figure(start_date, end_date):
    start_date = pd.to_datetime(start_date).date().isoformat()
    end_date = pd.to_datetime(end_date).date().isoformat()
    dff = df.copy()
    dff.rename(columns={"timestamp": "Date", "energy_consumed": "Energy Consumed"}, inplace=True)
    dff = dff.reindex(index=dff.index[::-1])
    dff["Day"] = dff.Date.astype('str').str.split(' ').str.get(0)

    dff.set_index('Day', inplace=True)
    dff = dff.loc[start_date:end_date:]
    figg = go.Figure(go.Scatter(x = dff['Date'], y = dff['Energy Consumed']))


    return figg

if __name__ == '__main__':
    app.run_server(debug=True)
