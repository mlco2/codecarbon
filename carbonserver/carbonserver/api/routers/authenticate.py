import base64
import logging
import random
from typing import Optional

import requests
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from fief_client import FiefAsync

from carbonserver.api.services.auth_service import (
    OptionalUserWithAuthDependency,
    UserWithAuthDependency,
)
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.config import settings
from carbonserver.container import ServerContainer

AUTHENTICATE_ROUTER_TAGS = ["Authenticate"]
LOGGER = logging.getLogger(__name__)
OAUTH_SCOPES = ["openid", "email", "profile"]
SESSION_COOKIE_NAME = "user_session"

router = APIRouter()

fief = FiefAsync(
    settings.fief_url, settings.fief_client_id, settings.fief_client_secret
)


@router.get("/auth/check", name="auth-check")
@inject
def check_login(
    auth_user: UserWithAuthDependency = Depends(OptionalUserWithAuthDependency),
    sign_up_service: SignUpService = Depends(Provide[ServerContainer.sign_up_service]),
):
    """
    return user data or redirect to login screen
    null value if not logged in
    """
    sign_up_service.check_jwt_user(auth_user.auth_user, create=True)
    return {"user": auth_user.auth_user}


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
        if "id_token" not in res.json():
            if "access_token" not in res.json():
                return Response(content="Invalid code", status_code=400)
            # get profile data from fief server if not present in response
            id_token = requests.get(
                settings.fief_url + "/api/userinfo",
                headers={"Authorization": "Bearer " + res.json()["access_token"]},
            ).json()
            sign_up_service.check_jwt_user(id_token)
        else:
            sign_up_service.check_jwt_user(res.json()["id_token"], create=True)

        creds = base64.b64encode(res.content).decode()
        base_url = request.base_url
        if settings.frontend_url != "":
            base_url = settings.frontend_url + "/"
        url = f"{base_url}home?auth=true&creds={creds}"

        # NOTE: RedirectResponse doesn't work with clevercloud
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

        response.set_cookie(
            SESSION_COOKIE_NAME,
            res.json()["access_token"],
            httponly=True,
            secure=False,
        )
        return response

    state = str(int(random.random() * 1000))
    url = f"{settings.fief_url}/authorize?response_type=code&client_id={settings.fief_client_id}&redirect_uri={login_url}&scope={' '.join(OAUTH_SCOPES)}&state={state}"
    return RedirectResponse(url=url)
