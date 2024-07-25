import base64
import logging
import random
from dataclasses import dataclass
from typing import Annotated, Optional

import requests
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import (
    APIKeyCookie,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2AuthorizationCodeBearer,
)
from fief_client import FiefAsync, FiefUserInfo
from fief_client.integrations.fastapi import FiefAuth

from carbonserver.api.schemas import Token, UserAuthenticate
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService
from carbonserver.config import settings

AUTHENTICATE_ROUTER_TAGS = ["Authenticate"]
LOGGER = logging.getLogger(__name__)
OAUTH_SCOPES = ["openid", "email", "profile"]

router = APIRouter()


@router.post(
    "/authenticate",
    tags=AUTHENTICATE_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Token,
)
@inject
def auth_user(
    user: UserAuthenticate,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> Token:
    verified_user = user_service.verify_user(user)
    if verified_user:
        return Token(access_token="a", token_type="access")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect password or email!",
    )


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
auth = fief_auth = FiefAuth(fief, scheme)
web_auth = FiefAuth(fief, web_scheme)
api_auth = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]


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
        self.user_service = user_service
        self.auth_user = auth_user
        try:
            self.db_user = user_service.get_user_by_id(auth_user["sub"])
        except Exception:
            self.db_user = None
        print("UserWithAuthDependency", auth_user, self.db_user)


@router.get("/auth/check", name="auth-check")
def check_login(
    user: FiefUserInfo = Depends(web_auth_with_redirect.current_user(optional=False)),
    sign_up_service: SignUpService = Depends(Provide[ServerContainer.sign_up_service]),
):
    """
    return user data or redirect to login screen
    null value if not logged in
    """
    sign_up_service.check_jwt_user(user["sub"], create=True)
    return {"user": user}


@router.get("/auth/auth-callback", name="auth_callback")
async def auth_callback(request: Request, response: Response, code: str = Query(...)):
    redirect_uri = request.url_for("auth_callback")
    tokens, _ = await fief.auth_callback(code, redirect_uri)
    response = RedirectResponse(request.url_for("auth-user"))
    response.set_cookie(
        SESSION_COOKIE_NAME,
        tokens["access_token"],
        max_age=tokens["expires_in"],
        httponly=True,
        secure=True,
    )
    return response


@router.get("/auth/login", name="login")
@inject
async def get_login(
    request: Request,
    state: Optional[str] = None,
    code: Optional[str] = None,
    sign_up_service: SignUpService = Depends(Provide[ServerContainer.sign_up_service]),
):
    """
    login and redirect to frontend app with token
    """
    login_url = request.url_for("login")
    if code:
        res = requests.post(
            f"{settings.fief_url}/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": login_url,
                "client_id": settings.fief_client_id,
                "client_secret": settings.fief_client_secret,
            },
        )

        # check if the user exists in local DB ; create if needed
        sign_up_service.check_jwt_user(res.json()["id_token"], create=True)
        url = f"{request.base_url}web/login#creds={base64.b64encode(res.content).decode()}"
        return RedirectResponse(url=url)

    state = str(int(random.random() * 1000))
    url = f"{settings.fief_url}/authorize?response_type=code&client_id={settings.fief_client_id}&redirect_uri={login_url}&scope={' '.join(OAUTH_SCOPES)}&state={state}"
    return RedirectResponse(url=url)
