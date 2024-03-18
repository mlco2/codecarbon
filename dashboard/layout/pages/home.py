import dash
from dash import html,dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', name="Home", order=0)


from data.data_functions import get_organization_list, get_project_list, get_team_list

##################### Get Data  ###########################

df_org = get_organization_list()
orga_id = df_org.id.unique().tolist()[1]
df_project = get_project_list(orga_id)
df_team = get_team_list(orga_id)
##################### PAGE LAYOUT ###########################
def layout():
      return html.Div(children=[
                                  html.Br(),
                                  html.H2(" About CodeCarbon  ",
                                          style={"text-align":"center"},
                                          #className="my-1"                                     
                                          ), 
                                  html.Hr(),
                                  dbc.Row(
                                    [ 
                                        dbc.Col([
                                              html.H3("Description: ",style={"text-align":"center"}, ),
                                              
                                        ]),
                                        dbc.Col([
                                              html.H6(
                                                "We created a Python package that estimates your hardware electricity power consumption (GPU + CPU + RAM) and we apply to it the carbon intensity of the region where the computing is done."                                              
                                              )

                                        ])
                                        
                                    ], justify="center",
                                  ),
                                  html.Hr(),
                                  dbc.Row([
                                       dbc.Col([
                                             dbc.Card(
                                                [
                                                    html.Img(src="/assets/calculation.png"),                                                  
                                                ],                                               
                                            )


                                       ]) 



                                  ]), 
                                  html.Hr(),
                                  dbc.Row(
                                    [
                                        dbc.Col([
                                              html.H6(
                                                "We explain more about this calculation in the Methodology section of the documentation. Our hope is that this package will be used widely for estimating the carbon footprint of computing, and for establishing best practices with regards to the disclosure and reduction of this footprint." 
                                                 
                                              )

                                        ])
                                        
                                    ], justify="center",
                                  ),
                                        
                                ]
                )

    