from datetime import datetime
from typing import Annotated, List

from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer, APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from fief_client import FiefAsync
from fief_client.integrations.cli import FiefAuth
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from carbonserver.carbonserver.config import settings


class OAuthHTTPMiddleware(BaseHTTPMiddleware):
    OAUTH_SCOPES = ["openid", "email", "profile"]
    exclude_paths: List[str] = []

    def __init__(
        self,
        app: ASGIApp,
    ):
        self.fief = FiefAsync(
            settings.fief_url, settings.fief_client_id, settings.fief_client_secret
        )
        self.web_scheme = APIKeyCookie(name=self.SESSION_COOKIE_NAME, auto_error=False)
        self.scheme = OAuth2AuthorizationCodeBearer(
            settings.fief_url + "/authorize",
            settings.fief_url + "/api/token",
            scopes={x: x for x in self.OAUTH_SCOPES},
            auto_error=False,
        )
        self.SESSION_COOKIE_NAME = "user_session"
        self.web_auth = FiefAuth(self.fief, self.web_scheme)
        self.api_auth = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]
        self.fief_auth = FiefAuth(self.fief, self.scheme)
        self.requests_count = {}

        super().__init__(app=app)

    def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host
        cookie = request.headers.get("Authorization")
        token = cookie.split(" ")[1]

        # Check if IP is already present in request_counts
        request_count, last_request = self.requests_count.get(client_ip, (0, datetime.min))

    async def _exclude_path(self, path: str) -> bool:
        """
        Checks if a path should be excluded from authentication

        :param path: The path to check
        :type path: str
        :return: True if the path should be excluded, False otherwise
        :rtype: bool
        """
        for pattern in self.exclude_paths:
            if pattern.match(path):
                return True
        return False
