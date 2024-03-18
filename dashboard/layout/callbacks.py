import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output 
from data.data_functions import (
    get_experiment,
    get_experiment_runs,
    get_experiment_sums,
    get_lastrun,
    get_orga_sums,
    get_organization_list,
    get_project,
    get_project_list,
    get_project_sums,
    get_run_emissions,
    get_run_info,
    get_run_sums,
    get_team_list,
)
from layout.app import app, df_mix
from layout.template import darkgreen, vividgreen
from plotly.subplots import make_subplots

from dash import Input, Output


import json
import os
import requests


API_PATH = os.getenv("CODECARBON_API_URL")
if API_PATH is None:
    #API_PATH = "https://api.codecarbon.io"
    API_PATH = "http://localhost:8008"   
USER = "jessica"
PSSD = "fake-super-secret-token"



# callback section: connecting the components
# ************************************************************************
# ************************************************************************

@app.callback(
                Output("output","children"),
                Output(component_id="organame", component_property="children"),
                Output(component_id="orgadesc", component_property="children"),

                Input("input_organame", "value"),

                Input("input_orgadesc", "value"),

                Input('submit_btn','n_clicks'),
               
)
def on_button_click(input_organame,input_orgadesc,n_clicks):  
        try: 
       
            if n_clicks:
                path = f"{API_PATH}/organization" 
                print(path)
                payload = {'name': input_organame , 'description' : input_orgadesc}
                response = requests.post(path, json=payload)
                
                if response.status_code == 201:
                    return f'You have entered "{input_organame}" and "{input_orgadesc}" into the database.' 
                else: 
                    if response.status_code == 405:
                        return f'You have entered "{response.status_code}"  and reason :  "{response.reason}"  '
                    else: 
                        return f'You have entered error :  "{response.status_code}"  and reason :  "{response.reason}" for path  {path} and payload {payload}'
        except:
                    return f'none'

#@app.callback(
##                Output("output2","children"),
#                Input("input_teamname", "value"),
#                Input("input_teamdesc", "value"),
#                Input(component_id="org-dropdown", component_property="value"),
#                Input('submit_btn_team','n_clicks'),
#)
#def on_button_click(input_teamname,input_teamdesc,n_clicks):

    #if n_clicks:
    #    return f'Input1 {input_teamname} and Input2 {input_teamdesc} and nb {n_clicks}' 
       

@app.callback(
    [
        Output(component_id="teamPicked", component_property="options"),
        # Output(component_id="projectPicked", component_property="value"),
    ],
    [
        Input(component_id="org-dropdown", component_property="value"),
    ],
)
def update_team_from_organization(value):
    orga_id = value
    df_team = get_team_list(orga_id)
    if len(df_team) > 0:
        # project_id = df_project.id.unique().tolist()[0]
        # project_name = df_project.name.unique().tolist()[0]
        options = [
            {"label": teamName, "value": teamId}
            for teamName, teamId in zip(df_team.name, df_team.id)
        ]
    else:
        # project_id = None
        # project_name = "No Project !!!"
        options = []

    return [options]



# indicators
# -------------------------------------------------------------------------


@app.callback(
    [
        Output(component_id="projectPicked", component_property="options"),
        # Output(component_id="projectPicked", component_property="value"),
    ],
    [
        Input(component_id="org-dropdown", component_property="value"),
    ],
)
def update_project_from_organization(value):
    orga_id = value
    df_project = get_project_list(orga_id)
    if len(df_project) > 0:
        # project_id = df_project.id.unique().tolist()[0]
        # project_name = df_project.name.unique().tolist()[0]
        options = [
            {"label": projectName, "value": projectId}
            for projectName, projectId in zip(df_project.name, df_project.id)
        ]
    else:
        # project_id = None
        # project_name = "No Project !!!"
        options = []
    # out=options
    # print("update_project_from_organization :", out)
    # return project_id, [options]
    return [options]


@app.callback(
    [
        Output(component_id="projectPicked", component_property="value"),
    ],
    [
        Input(component_id="projectPicked", component_property="options"),
    ],
)
def update_project_default_value(options):
    return [options[0]["value"]]


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
        Input(component_id="org-dropdown", component_property="value"),
    ],
)
def update_indicator(start_date, end_date, organization_id):
    orga_id = organization_id
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df_orga = get_orga_sums(orga_id, start_date, end_date)

    # Tot_Energy consumed card / Tot Emissions card / Tot_Duration cards
    if df_orga is None:
        Tot_energy_consumed = 0
        Tot_emissions = 0
        tot_duration_min = 0
    else:
        Tot_energy_consumed = str(round(df_orga["energy_consumed"], 2))
        Tot_emissions = str(round(df_orga["emissions"], 2))
        tot_duration_min = round(df_orga["duration"] / 60)
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
            if tot_duration_days >= 365:
                tot_duration_years = round(tot_duration_days / 365, 2)
                tot_duration = str(tot_duration_years)
                tot_duration_unit = "years"
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
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df_project = get_project_sums(project, start_date, end_date)

    if (df_project is None) or (len(df_project) != 15):
        energyConsumed = 0
        emission = 0
        duration = 0
    else:
        energyConsumed = df_project["energy_consumed"]
        emission = df_project["emissions"]
        duration = df_project["duration"]

    # Cards
    # --------------------------------------------------------------
    houseHold = str(round(100 * emission / 160.58, 2)) + " %"
    car = str(
        round(
            emission / 0.409,
        )
    )
    time_in_minutes = emission * (1 / 0.097) / 60
    tvTime = f"{time_in_minutes:.0f} min"
    if time_in_minutes >= 60:
        time_in_hours = time_in_minutes / 60
        tvTime = f"{time_in_hours:.0f} hours"
        if time_in_hours >= 24:
            time_in_days = time_in_hours / 24
            tvTime = f"{time_in_days:.0f} days"
    energy_project = str(round(energyConsumed, 2))
    emissions_project = str(round(emission, 2))
    duration_project = str(
        round(
            duration,
        )
    )
    duration_project = f"{duration:.0f}"
    duration_project_unit = "sec"
    if duration >= 60:
        duration_in_min = duration / 60
        duration_project = f"{duration_in_min:.0f}"
        duration_project_unit = "min"
        if duration_in_min >= 60:
            duration_in_hours = duration_in_min / 60
            duration_project = f"{duration_in_hours:.0f}"
            duration_project_unit = "H"
            if duration_in_hours >= 24:
                duration_in_days = duration_in_hours / 24
                duration_project = f"{duration_in_days:.0f}"
                duration_project_unit = "days"
                if duration_in_days >= 365:
                    duration_in_years = duration_in_days / 365
                    duration_project = f"{duration_in_years:.0f}"
                    duration_project_unit = "years"
    # #PieCharts in cards OUTPUT in return has to be changed
    # ----------------------------------------------------------------
    orga_id = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
    df_orga = get_orga_sums(orga_id, start_date, end_date)
    if df_orga is None:
        Total_orga_energy = 1
        Total_orga_emission = 1
        Total_orga_duration = 1
    else:
        Total_orga_energy = df_orga["energy_consumed"]
        Total_orga_emission = df_orga["emissions"]
        Total_orga_duration = df_orga["duration"]

    figPie = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
        subplot_titles=("KwH", "Kg eq. CO2", duration_project_unit),
    )
    figPie.add_trace(
        go.Pie(
            values=[energyConsumed, Total_orga_energy - energyConsumed],
            title="KwH",
        ),
        row=1,
        col=1,
    )
    figPie.add_trace(
        go.Pie(
            values=[emission, Total_orga_emission - emission],
            title="Kg eq.CO2",
        ),
        row=1,
        col=2,
    )
    figPie.add_trace(
        go.Pie(
            values=[duration, (Total_orga_duration - duration)],
            title=duration_project_unit,
        ),
        row=1,
        col=3,
    )
    figPie.update_layout(
        template="CodeCarbonTemplate",
        annotations=[
            dict(
                text=energy_project,
                x=0.15,
                y=0.45,
                font_size=20,
                showarrow=False,
            ),
            dict(text=emissions_project, x=0.5, y=0.45, font_size=20, showarrow=False),
            dict(
                text=duration_project,
                x=0.85,
                y=0.45,
                font_size=20,
                showarrow=False,
            ),
        ],
        margin=dict(l=10, r=10, b=10, t=10),
        height=200,
    )
    # BarChart
    # --------------------------------------------------------------------
    dfBar = get_experiment_sums(project, start_date, end_date)
    if dfBar.empty:
        dfBar = pd.DataFrame(
            [["", "", 0]], columns=["name", "experiment_id", "emissions"]
        )
    figBar = px.bar(
        dfBar, x="name", y="emissions", text="emissions", hover_name="experiment_id"
    )
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
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if clickPoint is None:
        lastrun = get_lastrun(project, start_date, end_date)
        if (lastrun is not None) and (len(lastrun) != 0):
            experiment_id = lastrun["experiment_id"]
            experiment_name = get_experiment(experiment_id)["name"]
        else:
            experiment_id = None
            experiment_name = None
    else:
        experiment_id = clickPoint["points"][0]["hovertext"]
        experiment_name = clickPoint["points"][0]["label"]

    df1 = pd.DataFrame()
    if experiment_id is not None:
        df1 = get_run_sums(experiment_id, start_date, end_date)
    if experiment_id is None or df1.empty:
        experiment_name = ""
        df1 = pd.DataFrame(
            [[start_date, 0, 0, 1, "/"], [end_date, 0, 0, 1, "/"]],
            columns=["timestamp", "emissions", "energy_consumed", "duration", "run_id"],
        )

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
        # Output(component_id="runMetadataTable", component_property="children"),
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
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df_run = pd.DataFrame()

    if experiment_clickPoint is None and clickPoint is None:
        last_run = get_lastrun(project, start_date, end_date)
        if (last_run is not None) and (len(last_run) != 0):
            run_name = last_run["id"]
            df_run, total_run = get_run_emissions(run_name)

    elif clickPoint is None:
        experiment_selected = experiment_clickPoint["points"][0]["hovertext"]
        run_list = get_experiment_runs(experiment_selected, start_date, end_date)
        if not run_list.empty:
            run_name = run_list["id"].iloc[-1]
            df_run, total_run = get_run_emissions(run_name)

    else:
        run_name = clickPoint["points"][0]["customdata"]
        df_run, total_run = get_run_emissions(run_name)

    if df_run.empty:
        run_name = ""
        df_run = pd.DataFrame(
            [[start_date, None], [end_date, None]],
            columns=["timestamp", "emissions_rate"],
        )

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
        + "<br><span style='font-size:0.8em;color:gray' >emissions rate (Kg eq. C02 per second)</span>",
        template="CodeCarbonTemplate",
    )
    line.update_xaxes(
        showgrid=False, showline=True, linewidth=2, linecolor="white", title=""
    )
    line.update_yaxes(
        showgrid=False,
        showline=True,
        linewidth=2,
        linecolor="white",
        title="emission rate",
    )

    clickPoint = None

    return line, clickPoint


# Metadata
# __________________________________________________________________________________________________
@app.callback(
    [
        Output(component_id="OS", component_property="children"),
        Output(component_id="python_version", component_property="children"),
        Output(component_id="CPU_count", component_property="children"),
        Output(component_id="CPU_model", component_property="children"),
        Output(component_id="GPU_count", component_property="children"),
        Output(component_id="GPU_model", component_property="children"),
        Output(component_id="longitude", component_property="children"),
        Output(component_id="latitude", component_property="children"),
        Output(component_id="region", component_property="children"),
        Output(component_id="provider", component_property="children"),
        Output(component_id="ram_tot", component_property="children"),
        Output(component_id="tracking_mode", component_property="children"),
    ],
    [
        Input(component_id="bubbleChart", component_property="clickData"),
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
        Input(component_id="barChart", component_property="clickData"),
        Input(component_id="projectPicked", component_property="value"),
    ],
)
def get_metadata_table(
    clickPoint, start_date, end_date, experiment_clickPoint, project
):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    dic_table = {
        "os": "",
        "python_version": "",
        "cpu_count": "",
        "cpu_model": "",
        "gpu_count": "",
        "gpu_model": "",
        "longitude": "",
        "latitude": "",
        "region": "",
        "provider": "",
        "ram_total_size": 0,
        "tracking_mode": "",
    }
    if experiment_clickPoint is None and clickPoint is None:
        last_run = get_lastrun(project, start_date, end_date)
        if (last_run is not None) and (len(last_run) != 0):
            run_name = last_run["id"]
            dic_table = get_run_info(run_name)
    elif clickPoint is None:
        experiment_selected = experiment_clickPoint["points"][0]["hovertext"]
        run_list = get_experiment_runs(experiment_selected, start_date, end_date)
        if not run_list.empty:
            run_name = run_list["id"].iloc[-1]
            dic_table = get_run_info(run_name)
    else:
        run_name = clickPoint["points"][0]["customdata"]
        dic_table = get_run_info(run_name)

    # if dic_table.empty:
    #    dic_table={'os':'','python_version':'','cpu_count':'','cpu_model':'','gpu_count':'','gpu_model':'', 'longitude':'','latitude':'','region':'','provider':'','ram_total_size':'','tracking_mode':''}

    return (
        dic_table["os"],
        dic_table["python_version"],
        dic_table["cpu_count"],
        dic_table["cpu_model"],
        dic_table["gpu_count"],
        dic_table["gpu_model"],
        dic_table["longitude"],
        dic_table["latitude"],
        dic_table["region"],
        dic_table["provider"],
        round(dic_table["ram_total_size"], 2),
        dic_table["tracking_mode"],
    )


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
    container = ""
    # Plotly Express
    if kpi == "My Project Emissions":
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df_em = get_experiment_sums(project, start_date, end_date)
        if not df_em.empty:
            df_em = (
                df_em.groupby(["country_iso_code", "country_name"])
                .agg({"emissions": "sum"})
                .reset_index()
            )
            df_em["emissions"] = round(df_em["emissions"], 2)
            df_em["project_name"] = get_project(project)["name"]
            orga_id = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
            project_em = get_orga_sums(orga_id, start_date, end_date)["emissions"]
        else:
            df_em = pd.DataFrame(
                columns=[
                    "country_iso_code",
                    "country_name",
                    "project_name",
                    "emissions",
                ]
            )
            project_em = 100
        fig = px.choropleth(
            data_frame=df_em,
            locationmode="ISO-3",
            locations="country_iso_code",
            scope="world",
            color="emissions",
            hover_data=["country_name", "project_name", "emissions"],
            color_continuous_scale=[vividgreen, darkgreen],
            range_color=[0, project_em],
            labels={"emissions": "CO2 emissions"},
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
            data_frame=df_mix,
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
            color_continuous_scale=["#c9fb37", "#024758", "#fb36c9"],
            labels={
                "Carbon intensity of electricity (gCO2/kWh)": "CO2 intensity (gCO2/kWh)"
            },
            template="CodeCarbonTemplate",
        )
        fig.update_coloraxes(
            colorbar_title_side="right", colorbar_title_text="CO2 intensity (gCO2/KwH)"
        )
        fig.update_geos(
            showland=True, landcolor="#6f898e", showocean=True, oceancolor="#759FA8"
        )
    return container, fig


# Refresh organizations list
@app.callback(
    [
        Output(component_id="org-dropdown", component_property="options"),
        Output(component_id="org-dropdown", component_property="value"),
    ],
    [Input("url-location", "pathname")],
)
def refresh_org_list(url):
    df_org = get_organization_list()
    org_id = df_org.id.unique().tolist()[1]
    options = [
        {"label": orgName, "value": orgId}
        for orgName, orgId in zip(df_org.name, df_org.id)
    ]
    return options, org_id
