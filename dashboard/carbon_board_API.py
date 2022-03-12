from datetime import date

import CodeCarbon_template
import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components import Components
from dash import dcc, html
from dash.dependencies import Input, Output
from data.data import (
    get_experiment_runs,
    get_experiment_sums,
    get_project_experiments,
    get_run_emissions,
    get_run_sums,
)
from plotly.subplots import make_subplots

# Common variables
# ******************************************************************************
# colors
darkgreen = "#024758"
vividgreen = "#c9fb37"
color3 = "#226a7a"
titleColor = "#d8d8d8"
# config (prevent default plotly modebar to appears, disable zoom on figures, set a double click reset ~ not working that good IMO )
config = {"displayModeBar": False, "scrollZoom": False, "doubleClick": "reset"}
CodeCarbon_template
# App
# *******************************************************************************
# *******************************************************************************
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

components = Components()
# data
# *******************************************************************************
df = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/dashboard/dashboard/new_emissions_df.csv"
)
df.timestamp = pd.to_datetime(df.timestamp)

df_mix = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/dashboard/dashboard/WorldElectricityMix.csv"
)


# Layout section: Bootstrap (https://hackerthemes.com/bootstrap-cheatsheet/)
# *******************************************************************************
app.layout = dbc.Container(
    [
        dbc.Row(
            [
            components.get_header(),
            components.get_global_summary()
            ]
        ),
        html.Div([  #hold project level information
        dbc.Row(
            dbc.Col(
                [
                    html.H5("Project :", ),
                    dbc.RadioItems(
                        id="projectPicked",
                        options=[
                            {"label": projectName, "value": projectId}
                            for projectName, projectId in zip(
                                df[["project_name", "project_id"]]
                                .drop_duplicates()
                                .iloc[:, 0],
                                df[["project_name", "project_id"]]
                                .drop_duplicates()
                                .iloc[:, 1],
                            )
                            #                            for projectName, projectId in df[['project_name','project_id']].drop_duplicates().iteritems()
                        ],
                        value=df.project_id.unique().tolist()[0],
                        inline=True,
#                        label_checked_class_name="text-primary",
#                        input_checked_class_name="border border-primary bg-primary",
                    ),
                ],
                width={"size": 6, "offset": 4},
            )
        ),
        dbc.Row(
            [
                # holding pieCharts
                dbc.Col(
                    dcc.Graph(id="pieCharts", config=config)
                    
                ),
                dbc.Col(
                    [
                        dbc.CardGroup([components.get_household_equivalent(), components.get_car_equivalent(),components.get_tv_equivalent()]),
                    ]
                ),
            ], 
            )
        ], className="shadow"),

        html.Div( # holding experiment related graph
        dbc.Row([dbc.Col(dcc.Graph(id="barChart", clickData=None, config=config)), # holding barChart
                dbc.Col(
                    dcc.Graph(
                        id="bubbleChart",
                        clickData=None,
                        hoverData=None,
                        figure={},
                        config=config,
                    ))
                    
            ]), className="shadow"),
        
        dbc.Row(
            [
                
                # holding line chart
                #dbc.Col(
                    dcc.Graph(id="lineChart", config=config)
                    #, width=6),
            ]
        ),
        # holding carbon emission map
        html.Br(),
        dcc.Dropdown(
            id="slct_kpi",
            options=[
                {
                    "label": "Global Carbon Intensity",
                    "value": "Global Carbon Intensity",
                },
                {"label": "My Carbon Emissions", "value": "My Carbon Emissions"},
            ],
            multi=False,
            value="Global Carbon Intensity",
            style={"width": "50%", "color": "black"},
            clearable=False,
        ),
        html.Div(id="output_container", children=[]),
        dcc.Graph(id="my_emission_map", figure={}, config=config),
    ]
)
# callback section: connecting the components
# ************************************************************************
# indicators
# -------------------------------------------------------------------------


@app.callback(
    [
        Output(component_id="Tot_Energy_Consumed", component_property="children"),
        Output(component_id="Tot_Emissions", component_property="children"),
        Output(component_id="Tot_Duration", component_property="children"),
        Output(component_id="Tot_Duration_unit", component_property="children"),
    ],
    [
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
    ],
)
def update_indicator(start_date, end_date):
    dff = df.copy()
    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
    # Tot_Energy consumed card
    Tot_energy_consumed = str(round(dff.energy_consumed.sum(), 2))
    # Tot Emissions card
    Tot_emissions = str(round(dff.emissions_sum.sum(), 2))
    # Tot_Duration cards
    tot_duration_min = round(dff.duration.sum() / 60)
    tot_duration = str(tot_duration_min)
    tot_duration_unit = "min"
    if tot_duration_min >= 60:
        tot_duration_hours = round(tot_duration_min / 60)
        tot_duration = str(tot_duration_hours)
        tot_duration_unit = "H"
        if tot_duration_hours >= 24:
            tot_duration_days = round(tot_duration_hours / 24)
            tot_duration = str(tot_duration_days)
            tot_duration_unit = "days"
    return Tot_energy_consumed, Tot_emissions, tot_duration, tot_duration_unit


# pieCharts and cards
# -----------------------------------------------------------------------------------
@app.callback(
    [
        Output(component_id="barChart", component_property="figure"),
        # Output(component_id='pieChartEnergy', component_property='figure'),
        # Output(component_id='pieChartEmissions', component_property='figure'),
        # Output(component_id='pieChartDuration', component_property='figure'),
        Output(component_id="pieCharts", component_property="figure"),
        Output(component_id="houseHold", component_property="children"),
        Output(component_id="car", component_property="children"),
        Output(component_id="tv", component_property="children"),
    ],
    [
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
        Input(component_id="projectPicked", component_property="value"),
    ],
)
def update_Charts(start_date, end_date, project):
    dff = df.copy()
    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    energyConsumed = dff[dff["project_id"] == project].energy_consumed.sum()
    emission = dff[dff["project_id"] == project].emissions_sum.sum()
    duration = dff[dff["project_id"] == project].duration.sum()
    # Cards
    # --------------------------------------------------------------
    houseHold = str(round(100 * emission / 160.58, 2)) + " %"
    car = str(
        round(
            emission / 0.409,
        )
    )
    time_in_minutes = emission * (1 / 0.097) * 60
    tvTime = str(time_in_minutes) + " min"
    if time_in_minutes >= 60:
        time_in_hours = time_in_minutes / 60
        tvTime = "{:.0f} hours".format(time_in_hours)
        if time_in_hours >= 24:
            time_in_days = time_in_hours / 24
            tvTime = "{:.0f} days".format(time_in_days)
    energy_project = str(round(energyConsumed, 2))
    emissions_project = str(round(emission, 2))
    duration_project = str(
        round(
            duration,
        )
    )
    duration_project_unit = "min"
    if duration >= 60:
        duration_in_hours = duration / 60
        duration_project = "{:.0f}".format(duration_in_hours)
        duration_project_unit = "H"
        if duration_in_hours >= 24:
            duration_in_days = duration_in_hours / 24
            duration_in_years = "{:.0f}".format(duration_in_days)
            duration_project_unit = "days"
            if duration_in_days >= 365:
                duration_in_years = duration_in_days / 365
                duration_project = "{:.0f}".format(duration_in_years)
                duration_project_unit = "year"
    # #PieCharts in cards OUTPUT in return has to be changed
    # ----------------------------------------------------------------
    # figPieEnergy = go.Figure([go.Pie(values=[energyConsumed, dff.energy_consumed.sum()-energyConsumed],
    #     textinfo='none',hole=.8,
    #     marker=dict(colors=[vividgreen, color3]), title='',hoverinfo='skip')])
    # figPieEnergy.update_layout(title_text='KwH',title_y=0.1,template = 'CodeCarbonTemplate' ,showlegend=False,
    #     margin=dict(r=0,l=0,t=0,b=0))
    # figPieEnergy.add_annotation(text=energy_project,font=dict(color='white',), x=0.5, y=0.5, font_size=20, showarrow=False)
    # figPieEmissions = go.Figure([go.Pie(values=[emission, dff.emissions_sum.sum()-emission],
    #     textinfo='none',hole=.8, marker=dict(colors=[vividgreen, color3]), title='',hoverinfo='skip')])
    # figPieEmissions.update_layout(title_text='kg eq.CO2',title_y=0.1,template = 'CodeCarbonTemplate' ,showlegend=False,margin=dict(r=0,l=0,t=0,b=0))
    # figPieEmissions.add_annotation(text=emissions_project,font=dict(color='white',), x=0.5, y=0.5, font_size=20, showarrow=False)
    # figPieDuration = go.Figure([go.Pie(values=[duration, (dff.duration.sum()-duration)],
    #     textinfo='none', hole=.8, marker=dict(colors=[vividgreen, color3]), title='',hoverinfo='skip')])
    # figPieDuration.update_layout(title_text=duration_project_unit, title_y=0.1,template = 'CodeCarbonTemplate' ,showlegend=False,margin=dict(r=0,l=0,t=0,b=0))
    # figPieDuration.add_annotation(text=duration_project,font=dict(color='white',), x=0.5, y=0.5, font_size=20, showarrow=False)
    figPie = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
        subplot_titles=("KwH", "Kg eq. CO2", duration_project_unit),
    )
    figPie.add_trace(
        go.Pie(
            values=[energyConsumed, dff.energy_consumed.sum() - energyConsumed],
            title="KwH",
            title_position="bottom center",
            textinfo="none",
            hole=0.8,
            marker=dict(colors=[vividgreen, color3]),
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    figPie.add_trace(
        go.Pie(
            values=[emission, dff.emissions_sum.sum() - emission],
            textinfo="none",
            hole=0.8,
            marker=dict(colors=[vividgreen, color3]),
            hoverinfo="skip",
            title="Kg eq.CO2",
            title_position="bottom center",
        ),
        row=1,
        col=2,
    )
    figPie.add_trace(
        go.Pie(
            values=[duration, (dff.duration.sum() - duration)],
            textinfo="none",
            hole=0.8,
            marker=dict(colors=[vividgreen, color3]),
            hoverinfo="skip",
            title=duration_project_unit,
            title_position="bottom center",
        ),
        row=1,
        col=3,
    )
    figPie.update_layout(
        template="CodeCarbonTemplate",
        showlegend=False,
        annotations=[
            dict(
                text=energy_project,
                font=dict(
                    color="white",
                ),
                x=0.15,
                y=0.5,
                font_size=20,
                showarrow=False,
            ),
            dict(text=emissions_project, x=0.5, y=0.5, font_size=20, showarrow=False),
            dict(
                text=duration_project,
                font=dict(
                    color="white",
                ),
                x=0.85,
                y=0.5,
                font_size=20,
                showarrow=False,
            ),
        ],
        margin=dict(l=10, r=10, b=10, t=10),
        height=200,
    )
    # barChart
    # --------------------------------------------------------------------
    #    dfBar = (
    #        dff[dff["project_id"] == project]
    #        .groupby("experiment_name")
    #        .agg(
    #            {
    #                "timestamp": min,
    #                "duration": sum,
    #                "emissions_sum": sum,
    #                "energy_consumed": sum,
    #                "experiment_description": lambda x: x.iloc[0],
    #            }
    #        )
    #        .reset_index()
    #    )
    #    figBar = px.bar(dfBar, x="experiment_name", y="emissions_sum", text="emissions_sum")
    # ADJUST WITH TIMESTAMP FILTER (start_date / end_date)
    dfBar = get_experiment_sums(project, start_date, end_date)
    if dfBar.empty:
        dfBar = pd.DataFrame([["","",0]],columns=["name","experiment_id","emissions"])
    figBar = px.bar(dfBar, x="name", y="emissions", text="emissions", hover_name="experiment_id")
    figBar.update_layout(
        title_text="Experiments emissions <br><span style='font-size:0.6em'>click a bar to filter bubble chart on the right side</span>",
        template="CodeCarbonTemplate",
        width=500,
        height=300,
    )
    figBar.update_traces(
        marker_color="#226a7a",
        marker_line_color=vividgreen,
        marker_line_width=3,
        texttemplate="%{text:.2f} Kg eq CO2",
        textposition="inside",
    )
    figBar.update_yaxes(showgrid=False, visible=False, title="")
    figBar.update_xaxes(
        showgrid=False, showline=True, linewidth=2, linecolor="white", title=""
    )
    return figBar, figPie, houseHold, car, tvTime


# BubbleCharts
# ---------------------------------------------------------------------------------------
@app.callback(
    [
        Output(component_id="bubbleChart", component_property="figure"),
        Output(component_id="barChart", component_property="clickData"),
    ],
    [
        Input(component_id="barChart", component_property="clickData"),
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
        Input(component_id="projectPicked", component_property="value"),
    ],
)
def uppdate_bubblechart(clickPoint, start_date, end_date, project):
#    dff = df.copy()
#    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    if clickPoint is None:
        experiment_id = get_project_experiments(project)["id"].iloc[-1]
        experiment_name = get_project_experiments(project)["name"].iloc[-1]
    else:
        experiment_id = clickPoint["points"][0]["hovertext"]
        experiment_name = clickPoint["points"][0]["label"]

#    df1 = (
#        dff[dff["experiment_name"] == experiment_name]
#        .groupby("run_id")
#        .agg(
#            {
#                "timestamp": "min",
#                "duration": "sum",
#                "emissions_sum": "sum",
#                "energy_consumed": "sum",
#            }
#        )
#        .reset_index()
#    )
    df1 = get_run_sums(experiment_id, start_date, end_date)
    if df1.empty:
        df1 = pd.DataFrame([[start_date,0,0,1,"/"],[end_date,0,0,1,"/"]],columns=["timestamp","emissions","energy_consumed","duration","run_id"])
    bubble = px.scatter(
        df1,
        x=df1.timestamp,
        y=df1.emissions,
        color=df1.energy_consumed,
        color_continuous_scale=[darkgreen, vividgreen],
        size=np.log(df1.duration),
        hover_name="run_id",
    )
    bubble.update_traces(
        customdata=df1.run_id, marker=dict(line=dict(color=vividgreen, width=3))
    )
    bubble.update_layout(
        title_text=experiment_name
        + "<br><span style='font-size:0.6em'>click a run to see timeseries</span>",
        height=300,
        template="CodeCarbonTemplate",
    )
    bubble.update_xaxes(
        showgrid=False, showline=False, linewidth=2, linecolor="white", title=""
    )
    bubble.update_yaxes(showgrid=False, title="emissions (kg eq.CO2)")
    bubble.update_coloraxes(
        colorbar_title_side="right", colorbar_title_text="energy consumed (KwH)"
    )
    clickPoint = None
    return bubble, clickPoint


# Line Chart
# ---------------------------------------------------------------------------------
@app.callback(
    [
        Output(component_id="lineChart", component_property="figure"),
        Output(component_id="bubbleChart", component_property="clickData"),
        #        Output(component_id="barChart", component_property="clickData"),
    ],
    [
        Input(component_id="bubbleChart", component_property="clickData"),
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
        Input(component_id="barChart", component_property="clickData"),
        Input(component_id="projectPicked", component_property="value"),
    ],
)
def uppdate_linechart(clickPoint, start_date, end_date, experiment_clickPoint, project):
    #    => ADD TIMESTAMP FILTERING
    if experiment_clickPoint is None and clickPoint is None:
#        default_experiment_id = get_project_experiments(project)["id"].iloc[-1]
#        Problem with experiment 'f763e8c0-c14e-40a1-a47c-b7106ef70378' => No Run!
        default_experiment_id = get_project_experiments(project)["id"].iloc[0]
        run_name = get_experiment_runs(default_experiment_id)["id"].iloc[-1]
    elif clickPoint is None:
        #    => CHECK EXPERIMENT_CLICK_POINT
        experiment_selected = experiment_clickPoint["points"][0]["hovertext"]
        run_name = get_experiment_runs(experiment_selected)["id"].iloc[-1]
    else:
        run_name = clickPoint["points"][0]["customdata"]

    #   API integration to get emissions at "run level"
    df_run, total_run = get_run_emissions(run_name)

    if df_run.empty:
        df_run = pd.DataFrame([[start_date,0],[end_date,0]],columns=["timestamp","emissions_rate"])

    line = px.line(
        df_run,
        x="timestamp",
        y="emissions_rate",
        color_discrete_sequence=[vividgreen],
        markers=True,
        symbol_sequence=["circle-open"],
    )
    line.update_layout(
        title_text=run_name
        + "<br><span style='font-size:0.8em;color:gray' >emissions (kg eq. C02)</span>",
        title_font_color=titleColor,
        template="CodeCarbonTemplate",
    )
    line.update_xaxes(
        showgrid=False, showline=True, linewidth=2, linecolor="white", title=""
    )
    line.update_yaxes(showgrid=False, showline=True, linewidth=2, linecolor="white", title="emission rate")
    clickPoint = None
    #    experiment_clickPoint = None
    return line, clickPoint  # , experiment_clickPoint


# Carbon Emission Map
# ---------------------------------------------------------------------------------
@app.callback(
    [
        Output(component_id="output_container", component_property="children"),
        Output(component_id="my_emission_map", component_property="figure"),
    ],
    [
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
        Input(component_id="projectPicked", component_property="value"),
        Input(component_id="slct_kpi", component_property="value"),
    ],
)
def update_map(start_date, end_date, project, kpi):
    dff = df.copy()
    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
    dff = dff[dff["project_id"] == project]
    dff = dff.groupby(["project_name", "country_iso_code", "country_name"]).agg(
        {"emissions_sum": "sum", "duration": "sum"}
    )
    #    dff["ratio"] = dff["emissions_sum"] / dff["duration"] * 3600 * 24
    dff = dff.reset_index()
    dff_mix = df_mix.copy()
    container = ""
    # Plotly Express
    if kpi == "My Carbon Emissions":
        fig = px.choropleth(
            data_frame=dff,
            locationmode="ISO-3",
            locations="country_iso_code",
            scope="world",
            color="emissions_sum",
            hover_data=["country_name", "emissions_sum", "project_name"],
            color_continuous_scale=[vividgreen, darkgreen],
            labels={"emissions_sum": "CO2 emissions"},
            template="CodeCarbonTemplate",
        )
        fig.update_coloraxes(
            colorbar_title_side="right", colorbar_title_text="CO2 emissions"
        )
        fig.update_geos(
            showland=True, landcolor="#898381", showocean=True, oceancolor="#759FA8"
        )
    elif kpi == "Global Carbon Intensity":
        fig = px.choropleth(
            data_frame=dff_mix,
            locationmode="ISO-3",
            locations="ISO",
            scope="world",
            color="Carbon intensity of electricity (gCO2/kWh)",
            hover_data=[
                "Country",
                "Carbon intensity of electricity (gCO2/kWh)",
                "% Fossil",
                "% Geothermal",
                "% Hydro",
                "% Nuclear",
                "% Solar",
                "% Wind",
            ],
            color_continuous_scale=px.colors.sequential.YlOrRd,
            labels={
                "Carbon intensity of electricity (gCO2/kWh)": "CO2 intensity (gCO2/kWh)"
            },
            template="CodeCarbonTemplate",
        )
        fig.update_coloraxes(
            colorbar_title_side="right", colorbar_title_text="CO2 intensity (gCO2/KwH)"
        )
        fig.update_geos(
            showland=True, landcolor="#898381", showocean=True, oceancolor="#759FA8"
        )
    return container, fig


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
