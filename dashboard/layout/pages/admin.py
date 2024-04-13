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
                                                id="Orgacard_to_hidden",
                                                children=
                                                [
                                                      dbc.CardHeader("Formulaire",style={"color":"#CDCDCD"}),
                                                      dbc.CardBody(
                                                          children=
                                                          [
                                                              html.H5(
                                                                        "Create an Organization :", style={"color":"white"}
                                                                    ), 
                                                                  html.Hr(),
                                                                  dcc.Input(id="input_organame", type="text", placeholder="Name"),
                                                                  html.Br(),
                                                                  dcc.Input(id="input_orgadesc", type="text", placeholder="Description"  ), 
                                                                  html.Br(),
                                                                  html.Br(),
                                                                  dbc.Button("submit", id="submit_btn", color="primary", n_clicks=0 ),
                                                          ],
                                                            style={"height": "10%", "border-radius": "10px", "border":"solid" , "border-color":"#CDCDCD" 
                                                                   },
                                                            className="shadow",
                                                            #value="on"
                                                      )
                                                      
                                                      

                                                ],style={"display":"block"} #make the card visible starting
                                              ),
                                              dbc.Card(
                                                 id="Output_text",
                                                 children=
                                                [
                                                      dbc.CardHeader("Result",style={"color":"#CDCDCD"} ),
                                                      dbc.CardBody(
                                                          [
                                                              
                                                                  html.Div(id='Output_data'),
                                                                 
                                                          ],style={"color":"#CDCDCD"} 
                                                            
                                                      ),
                                                      
                                                      

                                                ],style={"display":"none","color":"#CDCDCD"}
                                              ),



                                              
                                        ]),

                                        
                                    ]
            


                                  ),
                          html.Br(),
                                  dbc.Col([
                                              dbc.Card(
                                                id="Teamcard_to_hidden",
                                                children=
                                                [
                                                    
                                                      dbc.CardBody(
                                                          [
                                                              
                                                              html.H5(
                                                                    "Create a Team  :", style={"color":"white"}
                                                                ),                              
                                                             
                                                              dbc.Label("organization selected :  ",width=10 ,style={"color": "white"}, ),
                                                              #dcc.Dropdown(id='dropdown-div'),
                                                              dcc.Dropdown(
                                                                    #id="dropdown-div",
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
                                                ],style={"display":"none"}
                                              )
                                              
                                        ]),






                  #  html.Div([ 
                            
                  #               dcc.Input(id="input_organame", type="text", placeholder="Name"), 
                  #               html.Br(),
                  #               dcc.Input(id="input_orgadesc", type="text", placeholder="Description"),   
                  #               dbc.Button("submit", id="show-secret", color="primary",n_clicks=0),
                  #               #html.Div(id='err', style={'color':'red'}),
                  #               html.Div(id='body-div', children='Enter a value and press submit')

                  #           ])
                            



                  ]
    
                ),





