""" Implementation of the client credentials flow for fastapi """

import json

import requests

from carbonserver.api.schemas import Token, UserAuthenticate
from carbonserver.api.services.authentication.JWTBearer import JWKS, JWTBearer

JWKS_URL = "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs"


INITAL_ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ4TUlRaUpZR2EtYnpOS2FJOXc5dUNZU3g2RHBFcFJoUkpKWU5DakU1SU80In0.eyJleHAiOjE2Mjk2MzEwOTgsImlhdCI6MTYyOTYzMTAzOCwianRpIjoiODA2N2ZkOGYtZGE3OC00YWViLThiOGQtMjNlNjk3ODdmZjM2IiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2F1dGgvcmVhbG1zL21hc3RlciIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiJkZjBiZTFmMS1lYzkzLTRmNzAtYTg4ZS04YzkzMjYzNjVmOWEiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJiYWNrZW5kIiwic2Vzc2lvbl9zdGF0ZSI6IjEzOTYyOWI3LTQ5OTktNGMxOS05ZmYzLTFkOWNkNzE2YzE3OCIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLW1hc3RlciIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6InByb2ZpbGUgZW1haWwiLCJzaWQiOiIxMzk2MjliNy00OTk5LTRjMTktOWZmMy0xZDljZDcxNmMxNzgiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJBbWluZSBTYWJvbmkiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhbWluZS5zYWJvbmlAb2N0by5jb20iLCJnaXZlbl9uYW1lIjoiQW1pbmUiLCJmYW1pbHlfbmFtZSI6IlNhYm9uaSIsImVtYWlsIjoiYW1pbmUuc2Fib25pQG9jdG8uY29tIn0.SA0cS5dbpkiTqaEdnSQRR307PHVJfjjEPoHu3vy4F1lSQzTH8sPeNQ3r62H_IJUbb3oFg66a1fTwlk79b0SHT0csKHr--OV6U9rqTSo2Tn5nvqD6HL71CISxCixl9Mv6aGOXaIl2WQsysanzegn3R9d-YW2k8NZtvmsOLZtNL_psScj3Fzl8286XpNgT_ev3c09S5bqv9n4pqpuD1UIShKRmy3fHhsJ7z-mtBM6kKmC5D8UHP1bRDqGpI3ZFohbUnYvAd2ni3Hbl7786ALtk-riX8ce3SQXLv_n2o45DgIg5Wh1HpBlcM5_kKSrKi_ZDnIy5EB_wkBjzyZnURXOyjQ"

ACCESS_TOKEN_URL = (
    "http://localhost:8080/auth/realms/master/protocol/openid-connect/token"
)
SECRET_KEY = "641fccd7-ce3c-4f3a-83ef-ba0405d99b9f"

BASE_URL = "http://localhost:8080/auth/realms/master/"


class AuthenticationService:
    def __init__(self):
        self.browser_grant_type = "password"
        self.package_grant_type = "client_credentials"
        self.client_id = "backend"
        self.client_secret = SECRET_KEY
        self._login_url = BASE_URL + "protocol/openid-connect/token/"
        self._registration_url = (
            "http://localhost:8080/auth/realms/master/clients-registrations/default/"
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

        return Token(
            access_token=raw_response["access_token"],
            token_type=raw_response["token_type"],
        )

    def login_with_client_credentials(self, client_id, client_secret):
        login_request = requests.post(
            self._login_url,
            data={
                "grant_type": self.package_grant_type,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        raw_response = json.loads(login_request.content.decode("utf-8"))

        return Token(
            access_token=raw_response["access_token"],
            token_type=raw_response["token_type"],
        )

    def register_client(self, client_id: str, client_secret: str):
        register_request = requests.post(
            self._registration_url,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": INITAL_ACCESS_TOKEN,
            },
            data={
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
