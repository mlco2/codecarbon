import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, g, session
from flask_keycloak import FlaskKeycloak

# Read config path from cmd if provided.
config_path = "keycloak.json" if len(sys.argv) < 2 else sys.argv[1]
# Setup server.
server = Flask(__name__)
FlaskKeycloak.from_kc_oidc_json(server, config_path=config_path)
# Setup dash app.
app = dash.Dash(__name__, server=server)
app.layout = html.Div(
    id="main",
    children=[html.Div(id="greeting"), dcc.LogoutButton(logout_url="/logout")],
)


@app.callback(Output("greeting", "children"), [Input("main", "children")])
def update_greeting(input_value):
    user = session["userinfo"]
    return "Hello {} - calling from {}".format(
        user["preferred_username"], g.external_url
    )


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True, port=5006)
