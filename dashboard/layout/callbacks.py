import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from data.data import (
    get_experiment_runs,
    get_experiment_sums,
    get_orga_sums,
    get_project,
    get_project_experiments,
    get_project_list,
    get_project_sums,
    get_run_emissions,
    get_run_sums,
    get_lastrun,
    get_experiment,
)

# callback section: connecting the components
# ************************************************************************
# indicators
# -------------------------------------------------------------------------
from layout.app import app, df_mix

# colors
from layout.template import darkgreen, vividgreen
from plotly.subplots import make_subplots

# from layout.components import Components


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
        Output(component_id="Tot_Energy_Consumed", component_property="children"),
        Output(component_id="Tot_Emissions", component_property="children"),
        Output(component_id="Tot_Duration", component_property="children"),
        Output(component_id="Tot_Duration_unit", component_property="children"),
    ],
    [
        Input(component_id="periode", component_property="start_date"),
        Input(component_id="periode", component_property="end_date"),
        Input(component_id="org-dropdown", component_property="value")
    ],
)
def update_indicator(start_date, end_date, organization_id):
    #    dff = df.copy()
    #    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
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
    #    dff = df.copy()
    #    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    #    energyConsumed = dff[dff["project_id"] == project].energy_consumed.sum()
    #    emission = dff[dff["project_id"] == project].emissions_sum.sum()
    #    duration = dff[dff["project_id"] == project].duration.sum()
    df_project = get_project_sums(project, start_date, end_date)
    if df_project is None:
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
    time_in_minutes = emission * (1 / 0.097) * 60
    tvTime = "{:.0f} min".format(time_in_minutes)
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
    duration_project = "{:.0f}".format(duration)
    duration_project_unit = "sec"
    if duration >= 60:
        duration_in_min = duration / 60
        duration_project = "{:.0f}".format(duration_in_min)
        duration_project_unit = "min"
        if duration_in_min >= 60: 
            duration_in_hours = duration_in_min / 60
            duration_project = "{:.0f}".format(duration_in_hours)
            duration_project_unit = "H"
            if duration_in_hours >= 24:
                duration_in_days = duration_in_hours / 24
                duration_project = "{:.0f}".format(duration_in_days)
                duration_project_unit = "days"
                if duration_in_days >= 365:
                    duration_in_years = duration_in_days / 365
                    duration_project = "{:.0f}".format(duration_in_years)
                    duration_project_unit = "years"
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

    # ALL PROJECTS
    #    Total_project_en = dff.energy_consumed.sum()
    #    Total_project_em = dff.emissions_sum.sum()
    #    Total_project_du = dff.duration.sum()
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
    #    dff = df.copy()
    #    dff = dff[dff["timestamp"] > start_date][dff["timestamp"] < end_date]
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    if clickPoint is None:
        #experiment = get_project_experiments(project)
        lastrun = get_lastrun(project, start_date, end_date)
        if not (lastrun == None):
            experiment_id = lastrun["experiment_id"]
            experiment_name = get_experiment(experiment_id)["name"]
        else:
            experiment_id = None
            experiment_name = None
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
    df1 = pd.DataFrame()
    if experiment_id is not None:
        df1 = get_run_sums(experiment_id, start_date, end_date)
    if experiment_id is None or df1.empty:
        df1 = pd.DataFrame(
            [[start_date, 0, 0, 1, "/"], [end_date, 0, 0, 1, "/"]],
            columns=["timestamp", "emissions", "energy_consumed", "duration", "run_id"],
        )
        experiment_name = ''
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
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df_run = pd.DataFrame()
    if experiment_clickPoint is None and clickPoint is None:
        #        default_experiment_id = get_project_experiments(project)["id"].iloc[-1]
        #        Problem with experiment 'f763e8c0-c14e-40a1-a47c-b7106ef70378' => No Run!
        #default_experiment_id = get_project_experiments(project)["id"].iloc[0]
        #run_name = get_experiment_runs(default_experiment_id)["id"].iloc[-1]
        last_run = get_lastrun(project, start_date, end_date)
        if not (last_run == None):
            run_name = last_run["id"]
            df_run, total_run = get_run_emissions(run_name)
    elif clickPoint is None:
        #    => CHECK EXPERIMENT_CLICK_POINT
        experiment_selected = experiment_clickPoint["points"][0]["hovertext"]
        run_list = get_experiment_runs(experiment_selected, start_date, end_date)
        if not (run_list.empty):
            run_name = run_list["id"].iloc[-1]
            df_run, total_run = get_run_emissions(run_name)
    else:
        run_name = clickPoint["points"][0]["customdata"]
        df_run, total_run = get_run_emissions(run_name)

    #   API integration to get emissions at "run level"
    #df_run, total_run = get_run_emissions(run_name)

    if df_run.empty:
        df_run = pd.DataFrame(
            [[start_date, None], [end_date, None]],
            columns=["timestamp", "emissions_rate"],
        )
        run_name = ''

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
    container = ""
    # Plotly Express
    if kpi == "My Project Emissions":
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df_em = get_experiment_sums(project, start_date, end_date)
        if not (df_em.empty):
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
