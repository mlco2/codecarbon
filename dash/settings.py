APP_TITLE = "CodeCarbon Measure ML CO2 Emissions"

EXT_STYLESHEET = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

# Automatically define charts titles and Y label to filter data
LABELS = [
    {
        'x': 'timestamp',
        'y': 'emissions',
    },
    {
        'x': 'timestamp',
        'y': 'energy_consumed',
    },
    {
        'x': 'timestamp',
        'y': 'duration',
    },
]

FILTERS = [
    {
        'column': 'run_id',
        'button_type': 'dropdown',
        'sign': '==',
    },
    {
        'column': 'duration',
        'button_type': 'dropdown',
        'sign': '>=',
    },
    {
        'column': 'timestamp',
        'button_type': 'date-range',
    },
]
