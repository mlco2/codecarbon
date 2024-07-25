import base64
import logging
import random
from typing import Optional

import requests
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from fief_client import FiefUserInfo

from carbonserver.api.services.signup_service import SignUpService
from carbonserver.config import settings

from carbonserver.carbonserver.api.services.auth_service import fief, SESSION_COOKIE_NAME, scheme, \
    web_auth_with_redirect

AUTHENTICATE_ROUTER_TAGS = ["Authenticate"]
LOGGER = logging.getLogger(__name__)
OAUTH_SCOPES = ["openid", "email", "profile"]

router = APIRouter()


@router.get(
    "/auth/check",
    tags=AUTHENTICATE_ROUTER_TAGS,
    name="auth-check"
)
@inject
def check_login(
    user: FiefUserInfo = Depends(web_auth_with_redirect.current_user(optional=False)),
):
    """
    return user data or redirect to login screen
    null value if not logged in
    """
    return {"user": user}


@router.get(
    "/auth/auth-callback",
    tags=AUTHENTICATE_ROUTER_TAGS,
    name="auth_callback"
)
@inject
async def auth_callback(request: Request, response: Response, code: str = Query(...)):
    """
    update response with user auth data
    """
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


@router.get(
    "/auth/login",
    tags=AUTHENTICATE_ROUTER_TAGS,
    name="login"
)
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
