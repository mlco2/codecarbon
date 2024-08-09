from dataclasses import dataclass
from typing import Annotated, Optional

from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException
from fastapi.security import (
    APIKeyCookie,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2AuthorizationCodeBearer,
)
from fief_client import FiefAsync, FiefUserInfo
from fief_client.integrations.fastapi import FiefAuth
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from carbonserver.carbonserver.api.schemas import User
from carbonserver.carbonserver.api.services.user_service import UserService
from carbonserver.config import settings
from carbonserver.container import ServerContainer

fief = FiefAsync(
    settings.fief_url, settings.fief_client_id, settings.fief_client_secret
)
OAUTH_SCOPES = ["openid", "email", "profile"]

SESSION_COOKIE_NAME = "user_session"
scheme = OAuth2AuthorizationCodeBearer(
    settings.fief_url + "/authorize",
    settings.fief_url + "/api/token",
    scopes={x: x for x in OAUTH_SCOPES},
    auto_error=False,
)
web_scheme = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)
web_auth = FiefAuth(fief, web_scheme)
api_auth = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]

fief_auth = FiefAuth(fief, scheme)


@dataclass
class FullUser:
    db_user: dict
    auth_user: dict


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
    """

    def __init__(
        self,
        auth_user: Optional[FiefUserInfo] = Depends(
            fief_auth.current_user(optional=True)
        ),
        api_key: HTTPAuthorizationCredentials = Depends(web_scheme),
        user_service: UserService = Depends(Provide[ServerContainer.user_service]),
    ):
        self.auth_user: FiefUserInfo = auth_user
        try:
            self.db_user: User = user_service.get_user_by_id(auth_user["sub"])
        except Exception:
            self.db_user = None
        print("UserWithAuthDependency", auth_user, self.db_user)
