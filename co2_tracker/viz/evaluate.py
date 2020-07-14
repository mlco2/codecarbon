import os
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import convert
import locate


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def get_data(file):
    file = os.path.join(DIR_PATH, file)
    with open(file) as f:
        data = json.load(f)
    return data


def custom_emissions_comparison(process_kwh, locations, default_location):
    # TODO: Disambiguation of states such as Georgia, US and Georgia
    intl_data = get_data("../data/private_infra/2016/energy_mix.json")
    us_data = get_data("../data/private_infra/2016/us_emissions.json")
    emissions = []

    for location in locations:
        if locate.in_US(location):
            emission = convert.lbs_to_kgs(us_data[location]*convert.to_MWh(process_kwh))
            emissions.append((location, emission))
        else:
             c = intl_data[location]
             total, breakdown = c['total'], [c['coal'], c['petroleum'], \
             c['naturalGas'], c['lowCarbon']]
             if isinstance(total, float) and float(total) > 0:
                 breakdown = list(map(lambda x: 100*x/total, breakdown))
                 coal, petroleum, natural_gas, low_carbon = breakdown
                 breakdown = [convert.coal_to_carbon(process_kwh * coal/100),
                      convert.petroleum_to_carbon(process_kwh * petroleum/100),
                      convert.natural_gas_to_carbon(process_kwh * natural_gas/100), 0]
                 emission = sum(breakdown)
                 emissions.append((location, emission))

    return emissions


def default_emissions_comparison(process_kwh, default_location):
    # Calculates emissions in different locations

    intl_data = get_data("../data/private_infra/2016/energy_mix.json")
    global_emissions, europe_emissions, us_emissions = [], [], []

    # Handling international
    for country in intl_data:
           c = intl_data[country]
           total, breakdown = c['total'], [c['coal'], c['petroleum'], \
           c['naturalGas'], c['lowCarbon']]
           if isinstance(total, float) and float(total) > 0:
               breakdown = list(map(lambda x: 100*x/total, breakdown))
               coal, petroleum, natural_gas, low_carbon = breakdown
               breakdown = [convert.coal_to_carbon(process_kwh * coal/100),
                    convert.petroleum_to_carbon(process_kwh * petroleum/100),
                    convert.natural_gas_to_carbon(process_kwh * natural_gas/100), 0]
               emission = sum(breakdown)
               if locate.in_Europe(country):
                   europe_emissions.append((country,emission))
               else:
                   global_emissions.append((country,emission))

    global_emissions.sort(key=lambda x: x[1])
    europe_emissions.sort(key=lambda x: x[1])

    # Handling US
    us_data = get_data("../data/private_infra/2016/us_emissions.json")
    for state in us_data:
        if ((state != "United States") and state != "_units"):
            if us_data[state] != "lbs/MWh":
                emission = convert.lbs_to_kgs(us_data[state]*convert.to_MWh(process_kwh))
                us_emissions.append((state, emission))
    us_emissions.sort(key=lambda x: x[1])

    # getting max, median, and min
    max_global, max_europe, max_us = global_emissions[len(global_emissions)-1], \
        europe_emissions[len(europe_emissions)-1], us_emissions[len(us_emissions)-1]

    median_global, median_europe, median_us = global_emissions[len(global_emissions)//2], \
        europe_emissions[len(europe_emissions)//2], us_emissions[len(us_emissions)//2]

    min_global, min_europe, min_us= global_emissions[0], europe_emissions[0], us_emissions[0]

    comparison_values = [max_global, median_global, min_global, max_europe, \
        median_europe, min_europe, max_us, median_us, min_us]
    return comparison_values


def comparison_graphs(kwh, location, emissions):
    comparison_data = get_comparison_data(kwh)
    bar_charts_data = [comparison_data[6:], comparison_data[3:6], comparison_data[:3]]
    trace_names = ["Global", "Europe", "United States"]
    fig = make_subplots(rows=1, cols=3)

    chart_col = 1
    for data in bar_charts_data:
        comparison_values = bar_charts_data[chart_col-1]
        comparison_values.append([location, emissions])
        comparison_values.sort(key = lambda x: x[1])
        # bar chart colors
        colors = ['rgb(166, 189, 219)',] * 4
        labels = []
        data = []
        count = 0
        for pair in comparison_values:
            if pair[0] == location:
                colors[count] = 'rgb(28, 144, 153)'
            labels.append(pair[0])
            data.append(pair[1])
            count += 1
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
            col=chart_col
        )
        chart_col += 1

    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="United States",
        yaxis_title="CO2 (kg)",

        xaxis2_tickangle=-45,
        xaxis2_title="Europe",
        yaxis2_title="CO2 (kg)",

        xaxis3_tickangle=-45,
        xaxis3_title="Global (excluding Europe and US)",
        yaxis3_title="CO2 (kg)",
    )
    return fig


def get_comparison_data(kwh, locations=["Mongolia", "Iceland", "Switzerland"]):
    default_location = False
    if locations == ["Mongolia", "Iceland", "Switzerland"]:
        default_location = True
        comparison_values = default_emissions_comparison(kwh, default_location)
    else:
        comparison_values = custom_emissions_comparison(kwh, locations, default_location)

    return comparison_values
