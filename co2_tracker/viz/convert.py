""" UNIT OF MEASUREMENT CONVERSIONS """


def to_MWh(kwh):
    """ Converts from kilowatt-hours to megawatt-hours """
    return kwh / 1000


def coal_to_carbon(kwh):
    """
    2195.2 lbs CO2/MWh
    source: reverse-engineered from eGRID data
    """
    MWh = to_MWh(kwh)
    lbs_carbon = 2195.2 * MWh
    return lbs_to_kgs(lbs_carbon)


def natural_gas_to_carbon(kwh):
    """
    1639.89 lbs CO2/MWh
    source: reverse-engineered from eGRID data
    """
    MWh = to_MWh(kwh)
    lbs_carbon = 1639.89 * MWh
    return lbs_to_kgs(lbs_carbon)


def petroleum_to_carbon(kwh):
    """
    Oil: 1800.49 lbs CO2/MWh
    source: reverse-engineered from eGRID data
    """
    MWh = to_MWh(kwh)
    lbs_carbon = 1800.49 * MWh
    return lbs_to_kgs(lbs_carbon)


def lbs_to_kgs(lbs):
    """Convert from pounds to kilograms"""
    return lbs * 0.45359237


""" CARBON EQUIVALENCY """


def carbon_to_miles(kg_carbon):
    """
    8.89 × 10-3 metric tons CO2/gallon gasoline ×
    1/22.0 miles per gallon car/truck average ×
    1 CO2, CH4, and N2O/0.988 CO2 = 4.09 x 10-4 metric tons CO2E/mile
    Source: EPA
    """
    return kg_carbon / (4.09 * 10 ** (-7))  # number of miles driven by avg car


def carbon_to_home(kg_carbon):
    """
    Total CO2 emissions for energy use per home: 5.734 metric tons CO2 for electricity
    + 2.06 metric tons CO2 for natural gas + 0.26 metric tons CO2 for liquid petroleum gas
     + 0.30 metric tons CO2 for fuel oil  = 8.35 metric tons CO2 per home per year / 52 weeks
     = 160.58 kg CO2/week on average
    Source: EPA
    """
    return (
        kg_carbon / 160.58
    ) * 100  # percent of CO2 used in an avg US household in a week


def carbon_to_tv(kg_carbon):
    """
    Gives the amount of minutes of watching a 32-inch LCD flat screen tv required to emit and
    equivalent amount of carbon. Ratio is 0.097 kg CO2 / 1 hour tv
    """
    time_in_minutes = kg_carbon * (1 / 0.097) * 60
    formated_value = "{:.2g} minutes".format(time_in_minutes)
    if time_in_minutes >= 60:
        time_in_hours = time_in_minutes / 60
        formated_value = "{:.3g} hours".format(time_in_hours)
        if time_in_hours >= 24:
            time_in_days = time_in_hours / 24
            formated_value = "{:.2g} days".format(time_in_days)
    return formated_value
