""" Implementation of the client credentials flow for fastapi """

import json

import requests

from carbonserver.api.schemas import Token, UserAuthenticate
from carbonserver.api.services.authentication.JWTBearer import JWKS, JWTBearer

JWKS_URL = "http://localhost:8084/auth/realms/master/protocol/openid-connect/certs"

TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJsaERpU1ZMQU50WG5icmsxTU8yMlZuVzBvNG95YVVvZjRiZGtMRkRheFRRIn0.eyJleHAiOjE2MzMxNzI0NDgsImlhdCI6MTYzMzE3MjM4OCwianRpIjoiODA1NDNmOGEtMjg4ZS00ZDI0LTliNGEtODVhOTY4ZTYxYjIwIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2F1dGgvcmVhbG1zL21hc3RlciIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIwODE1Mzc2MS1kMzBmLTRhZGQtOTc4ZC01OTc0MDk4YTFmYTkiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJiYWNrZW5kIiwic2Vzc2lvbl9zdGF0ZSI6IjhhZWFjMThkLWMyOGYtNDAwNy1iNDczLTU4YTdiMWJiZTZlMyIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLW1hc3RlciIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6InByb2ZpbGUgZW1haWwiLCJzaWQiOiI4YWVhYzE4ZC1jMjhmLTQwMDctYjQ3My01OGE3YjFiYmU2ZTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicHJlZmVycmVkX3VzZXJuYW1lIjoidGVzdCIsImVtYWlsIjoidGVzdEB0ZXN0LmNvbSJ9.fA88EIGFM6_rNjOkjCDCuN35V3rX0s-Qupf7NdwOO2B9hodt6exXlaEdx_nJZOWtw9GEO6kq3Tb03vr4hW36kAkOFkpXMB3F6s5BpbXzRyvfrew8A9EEfMbq1IfAgGH5hU5RiIZdBktEuxw5bQe-R9oUXlw9ZyUDSJH4hWi-x7J84-g92HUgWswqwJOUTfXE1ms6-rszTtA6xyHfPxG8lWIMGl1HLJwcPpzF9LrMziLV0fRnDAUwQfI73DUw2HPZdSmmPExXI1aOndtFbfnBMq6I5tt7hg2gqt2KczG6ZnoECRpTqxZNJ8FsRBaoOXBy7E4vgdWFIIWUhpjl6o9Zi"

ACCESS_TOKEN_URL = (
    "http://localhost:8084/auth/realms/master/protocol/openid-connect/token"
)
SECRET_KEY = "cbb8a1b9-d79f-4b94-960a-c4d91c6eba0f"

BASE_URL = "http://localhost:8084/auth/realms/master/"


class AuthenticationService:
    def __init__(self):
        self.browser_grant_type = "password"
        self.package_grant_type = "client_credentials"
        self.client_id = "backend"
        self.client_secret = SECRET_KEY
        self._login_url = BASE_URL + "protocol/openid-connect/token/"
        self._registration_url = (
            "http://localhost:8084/auth/realms/master/clients-registrations/default/"
        )

        self.default_jwks = JWKS_URL

    def login(self, user_authenticate: UserAuthenticate):
        data = {
            "grant_type": self.browser_grant_type,
            "username": user_authenticate.email,
            "password": user_authenticate.password.get_secret_value(),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        login_request = requests.post(
            self._login_url,
            data=data,
        )
        raw_response = json.loads(login_request.content.decode("utf-8"))

        return Token(access_token=raw_response["access_token"])

    def register_client(self, client_id: str, client_secret: str):
        register_request = requests.post(
            self._registration_url,
            json={
                "clientId": client_id,
                "secret": client_secret,
                "directAccessGrantsEnabled": "true",
                "consentRequired": "false",
                "serviceAccountsEnabled": "true",
            },
        )
        client_configuration = json.loads(register_request.content.decode("utf-8"))

        return client_configuration


jwks_url = JWKS_URL
jwks = JWKS.parse_obj(requests.get(jwks_url).json())

auth = JWTBearer(jwks)
