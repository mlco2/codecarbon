import json
import logging
import re
import sys
import urllib.parse

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, Response, g, redirect, request, session
from keycloak import KeycloakGetError, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakConnectionError
from werkzeug.wrappers import Request

# from flask_keycloak import FlaskKeycloak

# Keycloak code taken from https://github.com/thedirtyfew/dash-keycloak/blob/master/flask_keycloak/core.py


logger = logging.getLogger("dash_keycloak")
logger.setLevel(logging.DEBUG)
# create stream handler which logs even debug messages
fh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)-12s: %(levelname)-8s %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.debug("GO!")


class Objectify(object):
    def __init__(self, **kwargs):
        self.__dict__.update({key.lower(): kwargs[key] for key in kwargs})


def check_match_in_list(patterns, to_check):
    if patterns is None or to_check is None:
        return False
    for pattern in patterns:
        if re.search(pattern, to_check):
            return True
    return False


class AuthHandler:
    def __init__(self, app, config, session_interface, keycloak_openid):
        self.app = app
        self.config = config
        self.session_interface = session_interface
        self.keycloak_openid = keycloak_openid
        # Create object representation of config.
        self.config_object = Objectify(config=config, **config)

    def is_logged_in(self, request):
        token = "token" in self.session_interface.open_session(
            self.config_object, request
        )
        logger.debug(f"{token=}")
        return token

    def auth_url(self, callback_uri):
        return self.keycloak_openid.auth_url(callback_uri)

    def login(self, request, response, **kwargs):
        try:
            # Get access token from Keycloak.
            token = self.keycloak_openid.token(**kwargs)
            # Get extra info.
            user = self.keycloak_openid.userinfo(token["access_token"])
            introspect = self.keycloak_openid.introspect(token["access_token"])
            # Bind info to the session.
            response = self.set_session(
                request, response, token=token, userinfo=user, introspect=introspect
            )
        except KeycloakAuthenticationError as e:
            return e.error_message, e.response_code

        return response

    def set_session(self, request, response, **kwargs):
        session = self.session_interface.open_session(self.config_object, request)
        for kw in kwargs:
            session[kw] = kwargs[kw]
        self.session_interface.save_session(self.config_object, session, response)
        return response

    def logout(self, response=None):
        self.keycloak_openid.logout(session["token"]["refresh_token"])
        session.clear()
        return response


class AuthMiddleWare:
    def __init__(
        self,
        app,
        auth_handler,
        redirect_uri=None,
        uri_whitelist=None,
        prefix_callback_path=None,
        abort_on_unauthorized=None,
        before_login=None,
    ):
        self.app = app
        self.auth_handler = auth_handler
        self._redirect_uri = redirect_uri
        self.uri_whitelist = uri_whitelist
        self.prefix_callback_path = prefix_callback_path
        self.before_login = before_login
        # Setup uris.
        self.callback_path = "/keycloak/callback"
        self.abort_on_unauthorized = abort_on_unauthorized

    def get_auth_uri(self, environ):
        return self.auth_handler.auth_url(self.get_callback_uri(environ))

    def get_callback_uri(self, environ):
        parse_result = urllib.parse.urlparse(self.get_redirect_uri(environ))
        callback_path = self.callback_path
        # Optionally, prefix callback path with current path.
        if self.prefix_callback_path:
            callback_path = parse_result.path + callback_path
        # Bind the uris.
        return parse_result._replace(path=callback_path).geturl()

    def get_redirect_uri(self, environ):
        if self._redirect_uri:
            return self._redirect_uri
        else:
            scheme = environ.get(
                "HTTP_X_FORWARDED_PROTO", environ.get("wsgi.url_scheme", "http")
            )
            host = environ.get("HTTP_X_FORWARDED_SERVER", environ.get("HTTP_HOST"))
            return f"{scheme}://{host}"

    def __call__(self, environ, start_response):
        response = None
        request = Request(environ)
        logger.debug(f"{request=}")
        # If the uri has been whitelisted, just proceed.
        if check_match_in_list(self.uri_whitelist, request.path):
            return self.app(environ, start_response)
        # If we are logged in, just proceed.
        if self.auth_handler.is_logged_in(request):
            return self.app(environ, start_response)
        # Before login hook.
        if self.before_login:
            response = self.before_login(
                request, redirect(self.get_redirect_uri(environ)), self.auth_handler
            )
            return response(environ, start_response)
        # On callback, request access token.
        if request.path == self.callback_path:
            kwargs = dict(
                grant_type=["public"],
                code=request.args.get("code", "unknown"),
                redirect_uri=self.get_callback_uri(environ),
            )
            response = self.auth_handler.login(
                request, redirect(self.get_redirect_uri(environ)), **kwargs
            )
        # If unauthorized, redirect to login page.
        if self.callback_path not in request.path:
            if check_match_in_list(self.abort_on_unauthorized, request.path):
                response = Response("Unauthorized", 401)
            else:
                response = redirect(self.get_auth_uri(environ))
        # Save the session.
        if response:
            logger.debug(f"{response=}")
            logger.debug(f"{start_response=}")
            # logger.debug(f"{environ=}")
            return response(environ, start_response)
        # Request is authorized, just proceed.
        return self.app(environ, start_response)


class FlaskKeycloak:
    def __init__(
        self,
        app,
        keycloak_openid,
        redirect_uri=None,
        uri_whitelist=None,
        logout_path=None,
        heartbeat_path=None,
        login_path=None,
        prefix_callback_path=None,
        abort_on_unauthorized=None,
        before_login=None,
    ):
        logout_path = "/logout" if logout_path is None else logout_path
        uri_whitelist = [] if uri_whitelist is None else uri_whitelist
        if heartbeat_path is not None:
            uri_whitelist = uri_whitelist + [heartbeat_path]
        if login_path is not None:
            uri_whitelist = uri_whitelist + [login_path]
        # Bind secret key.
        # if keycloak_openid._client_secret_key is not None:
        #     app.config["SECRET_KEY"] = keycloak_openid._client_secret_key
        # logger.debug(f"{app.config['SECRET_KEY']=}")
        # Add middleware.
        auth_handler = AuthHandler(
            app.wsgi_app, app.config, app.session_interface, keycloak_openid
        )
        auth_middleware = AuthMiddleWare(
            app.wsgi_app,
            auth_handler,
            redirect_uri,
            uri_whitelist,
            prefix_callback_path,
            abort_on_unauthorized,
            before_login,
        )

        def _save_external_url():
            g.external_url = auth_middleware.get_redirect_uri(request.environ)

        app.before_request(_save_external_url)
        app.wsgi_app = auth_middleware

        # Add logout mechanism.
        if logout_path:

            @app.route(logout_path, methods=["POST"])
            def route_logout():
                return auth_handler.logout(
                    redirect(auth_middleware.get_redirect_uri(request.environ))
                )

        if login_path:

            @app.route(login_path, methods=["POST"])
            def route_login():
                if request.json is None or (
                    "username" not in request.json or "password" not in request.json
                ):
                    return "No username and/or password was specified as json", 400
                return auth_handler.login(
                    request,
                    redirect(auth_middleware.get_redirect_uri(request.environ)),
                    **request.json,
                )

        if heartbeat_path:

            @app.route(heartbeat_path, methods=["GET"])
            def route_heartbeat_path():
                return "Chuck Norris can kill two stones with one bird."

    @staticmethod
    def from_kc_oidc_json(
        app,
        redirect_uri=None,
        config_path=None,
        logout_path=None,
        heartbeat_path=None,
        keycloak_kwargs=None,
        authorization_settings=None,
        uri_whitelist=None,
        login_path=None,
        prefix_callback_path=None,
        abort_on_unauthorized=None,
        debug_user=None,
        debug_roles=None,
    ):
        try:
            # Read config, assumed to be in Keycloak OIDC JSON format.
            config_path = "keycloak.json" if config_path is None else config_path
            with open(config_path, "r") as f:
                config_data = json.load(f)
            # Setup the Keycloak connection.
            keycloak_config = dict(
                server_url=config_data["auth-server-url"],
                realm_name=config_data["realm"],
                client_id=config_data["resource"],
                # client_secret_key=config_data["credentials"]["secret"],
                verify=config_data["ssl-required"] != "none",
            )
            if keycloak_kwargs is not None:
                keycloak_config = {**keycloak_config, **keycloak_kwargs}
            keycloak_openid = KeycloakOpenID(**keycloak_config)
            if authorization_settings is not None:
                keycloak_openid.load_authorization_config(authorization_settings)
        except FileNotFoundError as ex:
            before_login = _setup_debug_session(debug_user, debug_roles)
            # If there is not debug user and no keycloak, raise the exception.
            if before_login is None:
                raise ex
            # Create dummy object, we are bypassing keycloak anyway.
            keycloak_openid = KeycloakOpenID(
                "url", "name", "client_id", "client_secret_key"
            )
        return FlaskKeycloak(
            app,
            keycloak_openid,
            redirect_uri,
            logout_path=logout_path,
            heartbeat_path=heartbeat_path,
            uri_whitelist=uri_whitelist,
            login_path=login_path,
            prefix_callback_path=prefix_callback_path,
            abort_on_unauthorized=abort_on_unauthorized,
            before_login=_setup_debug_session(debug_user, debug_roles),
        )

    @staticmethod
    def try_from_kc_oidc_json(app, **kwargs):
        success = True
        try:
            FlaskKeycloak.from_kc_oidc_json(app, **kwargs)
        except FileNotFoundError:
            app.logger.exception(
                "No keycloak configuration found, proceeding without authentication."
            )
            success = False
        except IsADirectoryError:
            app.logger.exception(
                "Keycloak configuration was directory, proceeding without authentication."
            )
            success = False
        except KeycloakConnectionError:
            app.logger.exception(
                "Unable to connect to keycloak, proceeding without authentication."
            )
            success = False
        except KeycloakGetError:
            app.logger.exception(
                "Encountered keycloak get error, proceeding without authentication."
            )
            success = False
        return success


def _setup_debug_session(debug_user, debug_roles, debug_token="DEBUG_TOKEN"):
    def _before_login(request, response, auth_handler):
        return auth_handler.set_session(
            request,
            response,
            token=debug_token,
            userinfo=dict(preferred_username=debug_user),
            introspect=dict(realm_access=dict(roles=debug_roles)),
        )

    return _before_login if debug_user is not None else None


# Read config path from cmd if provided.
config_path = "keycloak.json" if len(sys.argv) < 2 else sys.argv[1]
# Setup server.
server = Flask(__name__)
logger.debug("Reading keycloak.conf")
FlaskKeycloak.from_kc_oidc_json(server, config_path=config_path)
print("Reading keycloak.conf successfull")
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
