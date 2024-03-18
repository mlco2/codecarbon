#import dash
#from dash import html
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from data.data_functions import get_organization_list, get_project_list
from dashboard.layout.components import Components 


dash.register_page(__name__, path='/codecarbon', name="Codecarbon", order=2 )


# Set configuration (prevent default plotly modebar to appears, disable zoom on figures, set a double click reset ~ not working that good IMO )
config = {
    "displayModeBar": True,
    "scrollZoom": False,
    "doubleClick": "reset",
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom",
        "pan",
        "select",
        "zoomIn",
        "zoomOut",
        "autoScale",
        "lasso2d",
    ],
}


# App
# *******************************************************************************
# *******************************************************************************


# Get organizations ans associated projects
df_org = get_organization_list()
orga_id = df_org.id.unique().tolist()[1]
df_project = get_project_list(orga_id)

# Load WorldElectricityMix
df_mix = pd.read_csv("./WorldElectricityMix.csv")



components = Components()


##################### PAGE LAYOUT ###########################
layout = html.Div(children=[
                  html.Br(),
                  html.H2("Code carbon Dashboard",  style={"text-align":"center"},),

     html.Div(
                [  # hold project level information
                    html.Img(src=""),
                    dbc.Row(
                          components.get_global_summary(),
                         # components.get_daterange(),

                    ),
                    dbc.Row(
                          components.get_daterange(),

                    ),
                    dbc.Row(
                        dbc.Col(
                            [  
                                html.Br(),
                                html.H5(
                                    "Organization :",
                                ),
                                dcc.Dropdown(
                                    id="org-dropdown",
                                    options=[
                                        {"label": orgName, "value": orgId}
                                        for orgName, orgId in zip(
                                            df_org.name, df_org.id
                                        )
                                    ],
                                    clearable=False,
                                    value=orga_id,
                                    # value=df_org.id.unique().tolist()[0],
                                    # value="Select your organization",
                                    style={"color": "black"},
                                    # clearable=False,
                                ),
                                html.H5(
                                    "Project :",
                                ),
                                dbc.RadioItems(
                                    id="projectPicked",
                                    options=[
                                        {"label": projectName, "value": projectId}
                                        for projectName, projectId in zip(
                                            df_project.name, df_project.id
                                        )
                                    ],
                                    value=df_project.id.unique().tolist()[-1]
                                    if len(df_project) > 0
                                    else "No projects in this organization !",
                                    inline=True,
                                    #                                label_checked_class_name="text-primary",
                                    #                                input_checked_class_name="border border-primary bg-primary",
                                ),
                            ],
                            width={"size": 6, "offset": 4},
                        )
                    ),
                    dbc.Row(
                        [
                            # holding pieCharts
                            dbc.Col(
                                dbc.Spinner(dcc.Graph(id="pieCharts", config=config))
                            ),
                            dbc.Col(
                                [
                                    dbc.CardGroup(
                                        [
                                            components.get_household_equivalent(),
                                            components.get_car_equivalent(),
                                            components.get_tv_equivalent(),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
                className="shadow",
            ),
            html.Div(  # holding experiment related graph
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(id="barChart", clickData=None, config=config)
                        ),  # holding barChart
                        dbc.Col(
                            dbc.Spinner(
                                dcc.Graph(
                                    id="bubbleChart",
                                    clickData=None,
                                    hoverData=None,
                                    figure={},
                                    config=config,
                                )
                            )
                        ),
                    ]
                ),
                className="shadow",
            ),
            html.Div(  # holding run level graph
                dbc.Row(
                    [
                        # holding line chart
                        dbc.Col(
                            dbc.Spinner(dcc.Graph(id="lineChart", config=config)),
                            width=6,
                        ),
                        dbc.Col(
                            dbc.Spinner(
                                html.Table(
                                    [
                                        html.Tr([html.Th("Metadata", colSpan=2)]),
                                        html.Tr(
                                            [
                                                html.Td("O.S."),
                                                html.Td(
                                                    id="OS",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Python Version"),
                                                html.Td(
                                                    id="python_version",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Number of C.P.U."),
                                                html.Td(
                                                    id="CPU_count",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("C.P.U. model"),
                                                html.Td(
                                                    id="CPU_model",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Number of G.P.U."),
                                                html.Td(
                                                    id="GPU_count",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("G.P.U. model"),
                                                html.Td(
                                                    id="GPU_model",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Longitude"),
                                                html.Td(
                                                    id="longitude",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Latitude"),
                                                html.Td(
                                                    id="latitude",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Region"),
                                                html.Td(
                                                    id="region",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Provider"),
                                                html.Td(
                                                    id="provider",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("RAM total size"),
                                                html.Td(
                                                    id="ram_tot",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("Tracking mode"),
                                                html.Td(
                                                    id="tracking_mode",
                                                    style={
                                                        "padding-top": "2px",
                                                        "padding-bottom": "2px",
                                                        "text-align": "right",
                                                    },
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            )
                        ),
                    ]
                ),
                className="shadow",
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
                    {"label": "My Project Emissions", "value": "My Project Emissions"},
                ],
                multi=False,
                value="Global Carbon Intensity",
                style={"width": "50%", "color": "black"},
                clearable=False,
            ),
            html.Div(id="output_container", children=[]),
            dcc.Graph(id="my_emission_map", figure={}, config=config),
            html.Div(
                [
                    html.Span("Powered by "),
                    html.A(
                        "Clever Cloud",
                        href="https://www.clever-cloud.com/",
                        target="_blank",
                    ),
                    html.Span("."),
                ],
                className="sponsor",
            ),




                    ]
                )

    