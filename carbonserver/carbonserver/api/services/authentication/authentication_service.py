""" Implementation of the client credentials flow for fastapi """

import json

import requests

from carbonserver.api.schemas import Token
from carbonserver.api.services.authentication.JWTBearer import JWKS, JWTBearer

JWKS_URL = "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs"

ACCESS_TOKEN_URL = (
    "http://localhost:8080/auth/realms/master/protocol/openid-connect/token"
)
SECRET_KEY = "3d926a66-7e6d-4281-9a95-54f40d13bf49"
ALGORITHM = "HS256"


class AuthenticationService:
    def __init__(self):
        self.grant_type = "password"
        self.client_id = "backend"
        self.client_secret = SECRET_KEY
        self._login_url = (
            "http://localhost:8080/auth/realms/master/protocol/openid-connect/token"
        )
        self.default_jwks = JWKS_URL

    def login(self, user_authenticate):
        login_request = requests.post(
            self._login_url,
            data={
                "grant_type": self.grant_type,
                "username": user_authenticate.email,
                "password": user_authenticate.password.get_secret_value(),
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        raw_response = json.loads(login_request.content.decode("utf-8"))
        print(raw_response)
        return Token(
            access_token=raw_response["access_token"],
            token_type=raw_response["token_type"],
        )


jwks_url = JWKS_URL
jwks = JWKS.parse_obj(requests.get(jwks_url).json())

auth = JWTBearer(jwks)
