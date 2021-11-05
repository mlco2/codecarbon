import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import date
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# colors
color1 = '#024758'
color2 = '#c9fb37'
color3 = '#226a7a'
darkgreen = '#024758'
vividgreen = '#c9fb37'
color3 = '#226a7a'
titleColor = '#d8d8d8'


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )

colors = {
    'background': '#024758',
    'text': 'white'
}


# data
# *******************************************************************************
df = pd.read_csv('new_emissions_df.csv')
df.timestamp = pd.to_datetime(df.timestamp)

# cards
# ******************************************************************************

card_household = dbc.Card([
                            dbc.CardImg(src="/assets/house_icon.png",
                                        top=True, bottom=False),
                            dbc.CardBody([
                                html.H4(id='houseHold'),
                                html.P("of an american household weekly energy consumption", className="card-title")])
                        ], color=color1, outline=False)

card_car = dbc.Card([
                            dbc.CardImg(src="/assets/car_icon.png",
                                        top=True, bottom=False),
                            dbc.CardBody([
                                html.H4(id='car'),
                                html.P("miles driven", className="card-title")])
                        ], color=color1, outline=False)

card_tv = dbc.Card([
                            dbc.CardImg(src="/assets/tv_icon.png",
                                        top=True, bottom=False),
                            dbc.CardBody([
                                html.H4(id='tv'),
                                html.P("of TV", className="card-title")])

                    ], color=color1, outline=False)


# Layout section: Bootstrap (https://hackerthemes.com/bootstrap-cheatsheet/)
# *******************************************************************************

app.layout = dbc.Container([
    dbc.Row([
        # holding logo, subtitle, date selector
        dbc.Col([
                html.Img(src='/assets/logo.png'),
                html.P('Track and reduce CO2 emissions from your computing'),
                dcc.DatePickerRange(id='periode',
                        day_size=39,
                        month_format='MMMM Y',
                        end_date_placeholder_text='MMMM Y',
                        # should be calculated from today() like minus 1 week
                        start_date=date(2020, 1, 1),
                        min_date_allowed=date(2000, 1, 1),
                        max_date_allowed=date.today(),
                        initial_visible_month=date.today(),
                        end_date=date.today())
        ], xs=12, sm=12, md=12, lg=4, xl=4),  # if small screen the col would take the full width
        # holding indicators graph
       dbc.Col(dcc.Graph(id='indicators'), xs=12, sm=12, md=12, lg=8, xl=8
       )
    ]),

    dbc.Row([
        # holding project selector
        dbc.Col(
                dcc.RadioItems(id='projectPicked',
                            options=[{'label': projectName, 'value': projectName}
                                for projectName in df.project_name.unique()],
                            value=df.project_name.unique().tolist()[0],
                            labelClassName="mr-3"
                             ), xs=12, sm=12, md=12, lg=4, xl=4


        ),
        # horlding pieCharts
        dbc.Col(
                dcc.Graph(id='pieCharts'), xs=12, sm=12, md=12, lg=8, xl=8
        )
    ]),

    dbc.Row([
        # holding cards

                    dbc.Col(card_household, width={"size": 2, "offset": 0}),
                    dbc.Col(card_car, width=2),
                    dbc.Col(card_tv, width=2),
                    #holding bar graph
                    dbc.Col(dcc.Graph(id='barChart',clickData=None,config={'scrollZoom':False, 'doubleClick':'reset'}),width={"size":6,"offset":0})
    ]),
    
    
     dbc.Row([
         #holding bubble chart
                dbc.Col(dcc.Graph(id='bubbleChart', clickData=None, hoverData=None, figure={}, 
                          config={'scrollZoom':False, 'doubleClick':'reset'}),width=6),
         #holding line chart
               dbc.Col(id='line_container', children=[], width=6)
                        
    ]),
         #holding carbon emission map
    html.Br(),
    dcc.Dropdown(id="slct_kpi",
                 options=[
                     {"label": "CO2_Emission", "value": "CO2_Emission"},
                     {"label": "Duration", "value": "Duration"},
                     {"label": "Ratio", "value": "Ratio"}],
                 multi=False,
                 value="CO2_Emission",
                 style={'width': "40%"}
                 ),
    html.Div(id='output_container', children=[]),
    dcc.Graph(id='my_emission_map', figure={})    

    ])


# callback section: connecting the components
# ************************************************************************

# indicators
# -------------------------------------------------------------------------
@ app.callback(
    Output(component_id='indicators', component_property='figure'),
    [Input(component_id='periode', component_property='start_date'),
    Input(component_id='periode', component_property='end_date')]
)
def update_indicator(start_date, end_date):

    dff = df.copy()
    dff = dff[dff['timestamp'] > start_date][dff['timestamp'] < end_date]

    # graph
    figIndic = make_subplots(rows=1, cols=3, specs=[
                    [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]])

    figIndic.add_trace(go.Indicator(value=dff.energy_consumed.sum(),
                         title={
                             "text": "Energy Consumed<br><span style='font-size:0.8em;color:gray'>kWh</span>"},
                          ), row=1, col=1)
    figIndic.add_trace(go.Indicator(value=dff.emissions_sum.sum(),
                           title={
                               "text": "Emissions<br><span style='font-size:0.8em;color:gray'>kg eq.C02</span>"},
                          ), row=1, col=2)
    figIndic.add_trace(go.Indicator(value=round(dff.duration.sum()/60, 0),
                           title={
                               "text": "Duration<br><span style='font-size:0.8em;color:gray'>min.</span>"},
                          ), 1, 3)

    figIndic.update_layout(
                    title_text="GLOBAL ",
                    title_font_color='#d8d8d8',

                    font=dict(color='white'),
                    height=250,
                    margin=dict(
                    l=10,
                    r=10,
                    b=10,
                    t=40,
                    pad=4
                    ),
                    paper_bgcolor=color1,
                    showlegend=False,
                    )

    return figIndic


# pieCharts and cards
# -----------------------------------------------------------------------------------

@ app.callback(
    [Output(component_id='barChart', component_property='figure'),
    Output(component_id='pieCharts', component_property='figure'),
    Output(component_id='houseHold', component_property='children'),
     Output(component_id='car', component_property='children'),
     Output(component_id='tv', component_property='children')
    ],
    [Input(component_id='periode', component_property='start_date'),
    Input(component_id='periode', component_property='end_date'),
    Input(component_id='projectPicked', component_property='value')]
)
def update_Charts(start_date, end_date, project):

    dff = df.copy()
    dff = dff[dff['timestamp'] > start_date][dff['timestamp'] < end_date]

    energyConsumed = dff[dff['project_name'] == project].energy_consumed.sum()
    emission = dff[dff['project_name'] == project].emissions_sum.sum()
    duration = dff[dff['project_name'] == project].duration.sum()
    
    ##Cards
    houseHold = str(round(100*emission/160.58, 2)) + " %"
    car = str(round(emission / 0.409, ))
    time_in_minutes = (emission * (1 / 0.097) * 60)
    tvTime = str(time_in_minutes) + " min"
    if time_in_minutes >= 60:
        time_in_hours = time_in_minutes / 60
        tvTime = "{:.0f} hours".format(time_in_hours)
        if time_in_hours >= 24:
            time_in_days = time_in_hours / 24
            tvTime = "{:.0f} days".format(time_in_days)
    string1 = str(round(energyConsumed, 2)) + ' KWh'
    string2 = str(round(emission, 2)) + ' kg eq.CO2'
    string3= str(round(duration,)) + ' min'
    if duration >= 60:
        duration_in_hours=duration/60
        string3="{:.0f} H".format(duration_in_hours)
        if duration_in_hours >= 24:
                duration_in_days=duration_in_hours/24
                string3="{:.0f} days".format(duration_in_days)
                if duration_in_days>=365:
                    duration_in_years = duration_in_days/365
                    string3='{:.0f} years'.format(duration_in_years)

    ##PieChart
    figPie=make_subplots(rows=1, cols=3, specs=[
                        [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]])
    figPie.add_trace(go.Pie(values=[energyConsumed, dff.energy_consumed.sum()-energyConsumed], name="energy consumed",
                     textinfo='none', hole=.8, marker=dict(colors=[color2, color3]), title=''), row=1, col=1)
    figPie.add_trace(go.Pie(values=[emission, dff.emissions_sum.sum(
    )-emission], name="emission", textinfo='none', hole=.8, marker=dict(colors=[color2, color3])), row=1, col=2)
    figPie.add_trace(go.Pie(values=[duration, (dff.duration.sum()-duration)], name="duration",
                     textinfo='none', hole=.8, marker=dict(colors=[color2, color3])), row=1, col=3)


    figPie.update_layout(
        title_text=project,
        title_font_color='#d8d8d8',
        font=dict(color='white'),
        paper_bgcolor=color1,
        showlegend=False,
        annotations=[dict(text=string1, font=dict(color='white',), x=0.05, y=0.5, font_size=20, showarrow=False), dict(
            text=string2, x=0.5, y=0.5, font_size=20, showarrow=False), dict(text=string3, font=dict(color='white',), x=0.93, y=0.5, font_size=20, showarrow=False), ],
        margin=dict(l=10, r=10, b=10, t=40, pad=4),
        height=200)
    #barChart
    dfBar = dff[dff['project_name']==project].groupby('experiment_name').agg({'timestamp': min, 'duration': sum, 'emissions_sum':sum, 'energy_consumed':sum, 'experiment_description': lambda x: x.iloc[0]}).reset_index()
    
    figBar = px.bar(dfBar, x='experiment_name', y='emissions_sum', text='emissions_sum')

    figBar.update_layout(
        title_text= project + " experiments emissions <br><span style='font-size:0.6em'>click a bar to filter bubble chart below </span>",
        title_font_color= titleColor,
        font= dict(color='white'),
        paper_bgcolor=darkgreen,
        plot_bgcolor=darkgreen,
        )
    figBar.update_traces(marker_color='#226a7a', marker_line_color=vividgreen,
                  marker_line_width=3, texttemplate='%{text:.2f} Kg eq CO2', textposition='outside')
    figBar.update_yaxes(showgrid=False, visible=False, title="")
    figBar.update_xaxes(showgrid=False, showline=True, linewidth=2, linecolor='white', title='')
    
    

    return figBar,figPie, houseHold, car, tvTime

# BubbleCharts
#---------------------------------------------------------------------------------------
@ app.callback(
    Output(component_id='bubbleChart', component_property='figure'),
    [Input(component_id='barChart', component_property='clickData'),
     Input(component_id='periode', component_property='start_date'),
     Input(component_id='periode', component_property='end_date'),
     Input(component_id='projectPicked', component_property='value')]
)

def uppdate_bubblechart(clickPoint, start_date, end_date,project):
    dff = df.copy()
    dff = dff[dff['timestamp'] > start_date][dff['timestamp'] < end_date]
    if clickPoint is None:
        experiment_name = dff[dff['project_name']==project]['experiment_name'].unique()[0]
    else:
        experiment_name = clickPoint['points'][0]['x']
    df1 = dff[dff['experiment_name']==experiment_name].groupby('run_id').agg({'timestamp':'min', 'duration':'sum','emissions_sum':'sum','energy_consumed':'sum'}).reset_index()
    
    bubble = px.scatter(df1, x=df1.timestamp, y=df1.emissions_sum, color=df1.energy_consumed, color_continuous_scale= [darkgreen, vividgreen],
                        size=np.log(df1.duration), hover_name='run_id')
    bubble.update_traces(customdata=df1.run_id,
                        marker=dict(line=dict(color=vividgreen, width=3)))
    bubble.update_layout(title_text= experiment_name +"<br><span style='font-size:0.6em'>click a run to see timeseries</span>",
                        title_font_color=titleColor,
                        font=dict(color='white'),
                        paper_bgcolor=darkgreen,
                        plot_bgcolor=darkgreen)
    bubble.update_xaxes(showgrid=False, showline=False, linewidth=2, linecolor='white', title='')
    bubble.update_yaxes(showgrid=False, title="emissions (kg eq.CO2)")
    bubble.update_coloraxes(colorbar_title_side='right', colorbar_title_text='energy consumed (KwH)')
    
    return bubble
# Line Chart
#---------------------------------------------------------------------------------
@ app.callback(
    Output(component_id='line_container', component_property='children'),
    Input(component_id='bubbleChart', component_property='clickData'),
     Input(component_id='periode', component_property='start_date'),
     Input(component_id='periode', component_property='end_date'),
     Input(component_id='barChart', component_property='clickData'),
     prevent_initial_call=True
    )

def uppdate_linechart(clickPoint, start_date, end_date,experiment_selected):
    dff = df.copy()
    dff = dff[dff['timestamp'] > start_date][dff['timestamp'] < end_date]
    
    if clickPoint is None:
        run_name = dff[dff['experiment_name']==experiment_selected]['run_id'].unique()[0]
    else:
        run_name= clickPoint['points'][0]['customdata']
    line = px.line(dff[dff['run_id']==run_name], x='timestamp', y ='emissions_sum',color_discrete_sequence=[vividgreen])
    line.update_layout(
        title_text= run_name +"<br><span style='font-size:0.8em;color:gray' >emissions (kg eq. C02)</span>",
        title_font_color= titleColor,
        font= dict(color='white'),paper_bgcolor=darkgreen,plot_bgcolor=darkgreen)
    line.update_xaxes(showgrid=False, showline=True, linewidth=2, linecolor='white',title='')
    line.update_yaxes(showgrid=False, visible=False, title="emissions (kg eq. C02)")
    
    
    return dcc.Graph(id='lineChart', figure=line)

# Carbon Emission Map
#---------------------------------------------------------------------------------
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='my_emission_map', component_property='figure')],
    [Input(component_id='periode', component_property='start_date'),
    Input(component_id='periode', component_property='end_date'),
    Input(component_id='projectPicked', component_property='value'),
    Input(component_id='slct_kpi', component_property='value')]
)
def update_map(start_date,end_date,project,kpi):
        
    dff = df.copy()
    dff = dff[dff['timestamp'] > start_date][dff['timestamp'] < end_date]
    dff = dff[dff['project_name'] == project]
    dff = dff.groupby(['project_name','country_iso_code','country_name']).agg({'emissions_sum':'sum','duration':'sum'})
    dff['ratio'] = dff['emissions_sum']/dff['duration']*3600*24
    dff = dff.reset_index()

    container = ""
    # Plotly Express
    if kpi == 'CO2_Emission':
        fig = px.choropleth(
            data_frame=dff,
            locationmode='ISO-3',
            locations='country_iso_code',
            scope="world",
            color='emissions_sum',
            hover_data=['country_name', 'emissions_sum', 'project_name'],
            color_continuous_scale=px.colors.sequential.YlOrRd,
            labels={'emissions_sum': 'Carbon Emission'},
#            template='plotly_white'
        )
    elif kpi == 'Duration':
        fig = px.choropleth(
            data_frame=dff,
            locationmode='ISO-3',
            locations='country_iso_code',
            scope="world",
            color='duration',
            hover_data=['country_name', 'duration', 'project_name'],
            color_continuous_scale=px.colors.sequential.YlOrRd,
            labels={'duration': 'Duration'},
#            template='plotly_white'
        )
    elif kpi == 'Ratio':        
        fig = px.choropleth(
            data_frame=dff,
            locationmode='ISO-3',
            locations='country_iso_code',
            scope="world",
            color='ratio',
            hover_data=['country_name', 'ratio', 'project_name'],
            color_continuous_scale=px.colors.sequential.YlOrRd,
            labels={'ratio': 'Ratio'},
#            template='plotly_white'
        )

    return container, fig

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
