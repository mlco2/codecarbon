import dash
from dash import html,dcc
import dash_bootstrap_components as dbc
from data.data_functions import get_organization_list, get_project_list, get_team_list



dash.register_page(__name__, path='/admin', name="Admin",order=1)



##################### Get Data  ###########################

df_org = get_organization_list()
orga_id = df_org.id.unique().tolist()[1]
df_project = get_project_list(orga_id)
df_team = get_team_list(orga_id)


##################### PAGE LAYOUT ###########################
def layout():   
    return html.Div(
                  id="app_container",
                  children=
                  [                 
                    html.Div(
                          id="sub_title",
                          children=[
                               html.Br(),
                              html.H2(  "Organization setting",
                                        style={"text-align":"center"},
                                      
                                      
                                      ),
                          ]

                      ),

                     html.Br(),
                                                       dbc.Row(
                                    [
                                        dbc.Col([
                                              dbc.Card(
                                                [
                                                    
                                                      dbc.CardBody(
                                                          [
                                                              html.H5(
                                                                        "Create an Organization :", style={"color":"white"}
                                                                    ), 
                                                                  html.Hr(),
                                                                  html.Div(id='output'),
                                                                  dcc.Input(id="input_organame", type="text", placeholder="Name", debounce=True ),
                                                                  html.Br(),
                                                                  dcc.Input(id="input_orgadesc", type="text", placeholder="Description" , debounce=True ), 
                                                                  html.Br(),
                                                                  html.Br(),
                                                                  dbc.Button("submit", id="submit_btn", color="primary", n_clicks=0 ),
                                                          ],
                                                            style={"height": "10%", "border-radius": "10px", "border":"solid" , "border-color":"#CDCDCD"  
                                                                   },
                                                            className="shadow"
                                                      ),
                                                      

                                                ]
                                              )
                                              
                                        ]),
                                        dbc.Col([
                                              dbc.Card(
                                                [
                                                    
                                                      dbc.CardBody(
                                                          [
                                                              
                                                              html.H5(
                                                                    "Create a Team  :", style={"color":"white"}
                                                                ),                              
                                                             
                                                              dbc.Label("organization selected :  ",width=10 ,style={"color": "white"}, ),
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
                                                                    style={"color": "black"},
                                                                ),
                                                              #html.Div(id='output2'),
                                                              html.Br(),


                                                              dcc.Input(id="input_teamname", type="text", placeholder="Name", debounce=True ),
                                                              html.Br(),
                                                              dcc.Input(id="input_teamdesc", type="text", placeholder="Description" , debounce=True ),
                                                              html.Br(),
                                                              html.Br(),
                                                              dbc.Button("submit", id="submit_btn_team", color="primary", n_clicks=0),
                                                          ],
                                                             style={"height": "10%", "border-radius": "10px", "border":"solid" , "border-color":"#CDCDCD" 
                                                                   },
                                                            className="shadow"
                                                      ),
                                                ]
                                              )
                                              
                                        ]),
                                        dbc.Col([
                                              dbc.Card(
                                                [
                                                    
                                                      dbc.CardBody(
                                                          [
                                                             
                                                              html.H5(
                                                                    "Create a project :", style={"color":"white"}
                                                                ),
                                                              dbc.Label("organization selected :  ",  width=10 , style={"color": "white"}),
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
                                                                dbc.Label("team selected :  ",  width=10 , style={"color": "white"} ),
                                                                dbc.RadioItems(
                                                                    id="teamPicked",
                                                                    options=[
                                                                        {"label": teamName, "value": teamId}
                                                                        for teamName, teamId in zip(
                                                                            df_team.name, df_team.id
                                                                        )
                                                                    ],
                                                                    value=df_team.id.unique().tolist()[-1]
                                                                    if len(df_team) > 0
                                                                    else "No team in this organization !",
                                                                    inline=True,
                                                                    style={"color": "white"}
                                                                    #                                label_checked_class_name="text-primary",
                                                                    #                                input_checked_class_name="border border-primary bg-primary",
                                                                ),

                                                              dbc.Label("Project ",  width=10, style={"color": "white"}),
                                                              #html.Div(id='output'),
                                                              dbc.Input(id="input_projectname", type="text", placeholder="Name", debounce=True ),
                                                              dbc.Input(id="input_projectdesc", type="text", placeholder="Description" , debounce=True ), 
                                                              html.Br(),
                                                              

                                                              
                                                              dbc.Button("submit", id="submit_btn_project", color="primary", n_clicks=0),
                                                          ],
                                                             style={"height": "10%", "border-radius": "10px", "border":"solid" , "border-color":"#CDCDCD" 
                                                                   },
                                                            className="shadow"
                                                      ),
                                                ]
                                              )
                                              
                                        ]),
                                        
                                        
                                    ]
            


                                  ),
 



                  ]
    
                ),


    