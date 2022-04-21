import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from data.data import get_organization_list, get_project_list
from layout.components import Components

# Common variables
# ******************************************************************************


# config (prevent default plotly modebar to appears, disable zoom on figures, set a double click reset ~ not working that good IMO )
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
# CodeCarbon_template
# App
# *******************************************************************************
# *******************************************************************************


# data
# *******************************************************************************
# df = pd.read_csv(
#    "https://raw.githubusercontent.com/mlco2/codecarbon/dashboard/dashboard/new_emissions_df.csv"
# )
# df.timestamp = pd.to_datetime(df.timestamp)

# SET ORGA_ID ans associated projects
# orga_id = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
df_org = get_organization_list()
# print(df_org)
orga_id = df_org.id.unique().tolist()[1]
# df_project = pd.DataFrame(columns=["name", "id"])
df_project = get_project_list(orga_id)
# print(f"orga_id={orga_id}")
df_mix = pd.read_csv(
    "https://raw.githubusercontent.com/mlco2/codecarbon/dashboard/dashboard/WorldElectricityMix.csv"
)


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
app.title = "Code Carbon"
components = Components()

# Layout section: Bootstrap (https://hackerthemes.com/bootstrap-cheatsheet/)
# *******************************************************************************
app.layout = dbc.Container(
    [
        dbc.Row([components.get_header(), components.get_global_summary()]),
        html.Div(
            [  # hold project level information
                html.Img(src=""),
                dbc.Row(
                    dbc.Col(
                        [
                            html.H5(
                                "Organization :",
                            ),
                            dcc.Dropdown(
                                id="org-dropdown",
                                options=[
                                    {"label": orgName, "value": orgId}
                                    for orgName, orgId in zip(df_org.name, df_org.id)
                                ],
                                # multi=False,
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
                                    # for projectName, projectId in df[['project_name','project_id']].drop_duplicates().iteritems()
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
                            # dbc.Spinner(
                            dcc.Graph(id="pieCharts", config=config)
                            #    )
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
                        # dbc.Spinner(
                        dcc.Graph(
                            id="bubbleChart",
                            clickData=None,
                            hoverData=None,
                            figure={},
                            config=config,
                        )
                        # )
                    ),
                ]
            ),
            className="shadow",
        ),
        html.Div(  # holding run level graph
            dbc.Row(
                [
                    # holding line chart
                    # dbc.Col(
                    # dbc.Spinner(
                    dcc.Graph(id="lineChart", config=config)
                    #    )
                    # , width=6),
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
