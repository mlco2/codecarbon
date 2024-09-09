from dataclasses import dataclass
from typing import Optional

import jwt
from container import ServerContainer
from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyCookie, HTTPBearer, OAuth2AuthorizationCodeBearer
from fief_client import FiefAsync, FiefUserInfo
from fief_client.integrations.fastapi import FiefAuth
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from carbonserver.api.services.user_service import UserService
from carbonserver.config import settings

OAUTH_SCOPES = ["openid", "email", "profile"]
fief = FiefAsync(
    settings.fief_url, settings.fief_client_id, settings.fief_client_secret
)


@dataclass
class FullUser:
    db_user: dict
    auth_user: dict


SESSION_COOKIE_NAME = "user_session"
scheme = OAuth2AuthorizationCodeBearer(
    settings.fief_url + "/authorize",
    settings.fief_url + "/api/token",
    scopes={x: x for x in OAUTH_SCOPES},
    auto_error=False,
)
web_scheme = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)
fief_auth_cookie = FiefAuth(fief, web_scheme)


class UserOrRedirectAuth(FiefAuth):
    client: FiefAsync

    async def get_unauthorized_response(self, request: Request, response: Response):
        redirect_uri = request.url_for("auth_callback")
        auth_url = await self.client.auth_url(redirect_uri, scope=OAUTH_SCOPES)

        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": str(auth_url)},
        )


web_auth_with_redirect = UserOrRedirectAuth(fief, web_scheme)


class UserWithAuthDependency:
    """
    Used to reconciliate oauth and db sides for a user
    Auth token can be passed as bearer token or cookie
    """

    def __init__(
        self,
        auth_user_cookie: Optional[FiefUserInfo] = Depends(
            fief_auth_cookie.current_user(optional=True)
        ),
        cookie_token: Optional[str] = Depends(web_scheme),
        # api_key: Optional[HTTPAuthorizationCredentials] = Depends(web_scheme),
        bearer_token: Optional[str] = Depends(HTTPBearer(auto_error=False)),
        user_service: Optional[UserService] = Depends(
            Provide[ServerContainer.user_service]
        ),
    ):
        self.user_service = user_service

        if cookie_token is not None:
            self.auth_user = jwt.decode(
                cookie_token, options={"verify_signature": False}, algorithms=["HS256"]
            )
        elif bearer_token is not None and settings.environment == "develop":
            self.auth_user = jwt.decode(
                bearer_token.credentials,
                settings.jwt_key,
                algorithms=[
                    "HS256",
                ],
            )
        else:
            self.auth_user = None

        try:
            self.db_user = user_service.get_user_by_id(self.auth_user["sub"])
        except Exception:
            self.db_user = None
