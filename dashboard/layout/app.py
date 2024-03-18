import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from data.data_functions import get_organization_list, get_project_list
from layout.components import Components

# Common variables
# ******************************************************************************
# *******************************************************************************


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

# Define application
app = dash.Dash(
    __name__,
    pages_folder='pages',
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
app.title = "Code Carbon"
components = Components()


# Layout section: Bootstrap (https://hackerthemes.com/bootstrap-cheatsheet/)
# *******************************************************************************
# *******************************************************************************
def serve_layout():
    return dbc.Container(
        [
            dbc.Row(
                        [ components.get_header()  ] #, components.get_global_summary() ]
                   ),    
            dbc.Row([
                        dbc.Navbar(
                                dbc.Container([
                                    dbc.Nav([
                                                dbc.NavLink(page['name'] , href=page['path'])\
                                                for page in dash.page_registry.values()
                                                if not page['path'].startswith("/app")

                                            ]),


                                    ], fluid=True
                                ),
                                #style={"border":"solid" , "border-color":"#CDCDCD"},
                                dark=False,
                                color="#CDCDCD",
                                    
                              
                        ),
                    ]
            ),
            dbc.Row(                 
                      dash.page_container 
                   )              
        ]
    )
