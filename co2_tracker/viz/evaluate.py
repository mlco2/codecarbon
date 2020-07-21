import os
import json

import convert
import locate


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def get_data(file):
    file = os.path.join(DIR_PATH, file)
    with open(file) as f:
        data = json.load(f)
    return data


def energy_mix(location, intl_mix, us_mix):
    """ Gets the energy mix information for a specific location

        Parameters:
            location (str): user's location
            location_of_default (str): Specifies which average to use if
            	location cannot be determined

        Returns:
            breakdown (list): percentages of each energy type
    """
    if locate.in_US(location):
        s = us_mix[location]['mix']
        coal, oil, natural_gas = s['coal']*100, s['oil']*100, s['gas']*100
        nuclear, hydro, biomass, wind, solar, geo, = \
        s['nuclear'], s['hydro'], s['biomass'], s['wind'], \
        s['solar'], s['geothermal']

        low_carbon = sum([nuclear,hydro,biomass,wind,solar,geo])*100
        mix_data = [['Coal', "{:.2f}".format(coal)],
                    ['Oil', "{:.2f}".format(oil)],
                    ['Natural Gas', "{:.2f}".format(natural_gas)],
                    ['Low Carbon', "{:.2f}".format(low_carbon)]]

        return mix_data

    else:
        c = intl_mix[location] # get country
        total, breakdown =  c['total'], [c['coal'], c['petroleum'], \
        c['naturalGas'], c['lowCarbon']]

        breakdown = list(map(lambda x: 100*x/total, breakdown))
        coal, petroleum, natural_gas, low_carbon = breakdown
        mix_data = [['Coal',  "{:.2f}".format(coal)],
                    ['Petroleum', "{:.2f}".format(petroleum)],
                    ['Natural Gas', "{:.2f}".format(natural_gas)],
                    ['Low Carbon', "{:.2f}".format(low_carbon)]]

        return mix_data


def custom_emissions_comparison(process_kwh, locations, intl_mix, us_data):
    # TODO: Disambiguation of states such as Georgia, US and Georgia
    emissions = []

    for location in locations:
        if locate.in_US(location):
            emission = convert.lbs_to_kgs(us_data[location]*convert.to_MWh(process_kwh))
            emissions.append((location, emission))
        else:
             c = intl_mix[location]
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


def default_emissions_comparison(process_kwh, intl_mix, us_data):
    # Calculates emissions in different locations
    global_emissions, europe_emissions, us_emissions = [], [], []

    # Handling international
    for country in intl_mix:
           c = intl_mix[country]
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


def get_comparison_data(kwh, intl_mix, us_data, locations=["Mongolia", "Iceland", "Switzerland"],
                        default_location=False):
    if default_location == True:
        comparison_values = default_emissions_comparison(kwh, intl_mix, us_data)
    else:
        comparison_values = custom_emissions_comparison(kwh, locations, intl_mix, us_data)

    return comparison_values
