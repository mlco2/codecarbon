APP_TITLE = "CodeCarbon Measure ML CO2 Emissions"

EXT_STYLESHEET = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

# User menu filters
# Note: Requires to add corresponding components in file "filters"
# in function "menu_filters"
FILTERS = [
    {
        'column': 'run_id',
        'button_type': 'dropdown',
        'sign': '==',
    },
    {
        'column': 'emissions',
        'button_type': 'dropdown',
        'sign': '>=',
    },
    {
        'column': 'timestamp',
        'button_type': 'date-range',
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
]
