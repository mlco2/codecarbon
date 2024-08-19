import base64
import logging
import random
from typing import Optional

import jwt
import requests
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from fief_client import FiefUserInfo

from carbonserver.api.services.signup_service import SignUpService
from carbonserver.carbonserver.api.services.auth_service import (
    OAUTH_SCOPES,
    SESSION_COOKIE_NAME,
    fief,
    web_auth_with_redirect,
)
from carbonserver.config import settings

AUTHENTICATE_ROUTER_TAGS = ["Authenticate"]
LOGGER = logging.getLogger(__name__)


router = APIRouter()


@router.get("/auth/check", tags=AUTHENTICATE_ROUTER_TAGS, name="auth-check")
@inject
def check_login(
    user: FiefUserInfo = Depends(web_auth_with_redirect.current_user(optional=False)),
):
    """
    return user data or redirect to login screen
    null value if not logged in
    """
    return {"user": user}


@router.get("/auth/auth-callback", tags=AUTHENTICATE_ROUTER_TAGS, name="auth_callback")
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


@router.get("/auth/login", tags=AUTHENTICATE_ROUTER_TAGS, name="login")
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
        if "id_token" not in res.json():
            # get profile data from fief server if not present in response
            id_token = requests.get(
                settings.fief_url + "/api/userinfo",
                headers={"Authorization": "Bearer " + res.json()["access_token"]},
            ).json()
            sign_up_service.check_jwt_user(id_token)
        else:
            sign_up_service.check_jwt_user(res.json()["id_token"], create=True)

        print("=> 100 sign up check done")
        creds = base64.b64encode(res.content).decode()
        print("=> 120")
        url = f"{request.base_url}home?auth=true&creds={creds}"
        print("=> 150 redir url", url)
        # response = RedirectResponse(url=url)
        content = f"""<html>
        <head>
        <script>
        window.location.href = "{url}";
        </script>
        </head>
        </html>
        """
        response = Response(content=content)
        print(url)
        print(response)
        print("=> 200")
        response.set_cookie(
            SESSION_COOKIE_NAME,
            res.json()["access_token"],
            httponly=True,
            secure=False,
        )
        print("=> 250")
        print(response)
        return response

    state = str(int(random.random() * 1000))
    url = f"{settings.fief_url}/authorize?response_type=code&client_id={settings.fief_client_id}&redirect_uri={login_url}&scope={' '.join(OAUTH_SCOPES)}&state={state}"
    return RedirectResponse(url=url)
