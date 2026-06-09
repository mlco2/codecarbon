import base64
import json
import logging
from typing import Optional

from authlib.integrations.starlette_client import OAuthError
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse

from carbonserver.api.services.auth_providers.oidc_auth_provider import (
    OIDCAuthProvider,
)
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
@inject
async def auth_callback(
    request: Request,
    response: Response,
    code: str = Query(...),
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    if auth_provider is None:
        raise HTTPException(status_code=501, detail="Authentication not configured")
    redirect_uri = request.url_for("auth_callback")
    tokens, _ = await auth_provider.handle_auth_callback(code, str(redirect_uri))
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
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    """
    login and redirect to frontend app with token
    """
    if auth_provider is None:
        raise HTTPException(status_code=501, detail="Authentication not configured")
    login_url = request.url_for("login")
    if code:
        try:
            token = await auth_provider.client.authorize_access_token(request)
        except OAuthError:
            return "Error"

        # check if the user exists in local DB ; create if needed
        if "id_token" not in token:
            if "access_token" not in token:
                return Response(content="Invalid code", status_code=400)
            # get profile data from auth provider if not present in response
            id_token = await auth_provider.get_user_info(token["access_token"])
            sign_up_service.check_jwt_user(id_token)
        else:
            sign_up_service.check_jwt_user(token["id_token"], create=True)
        user = token.get("userinfo")
        if user:
            request.session["user"] = dict(user)

        creds = base64.b64encode(json.dumps(token).encode()).decode()
        base_url = request.base_url
        if settings.frontend_url != "":
            base_url = settings.frontend_url + "/"
        url = f"{base_url}home?auth=true&creds={creds}"
        response = auth_provider.create_redirect_response(url)

        response.set_cookie(
            SESSION_COOKIE_NAME,
            token["access_token"],
            httponly=True,
            secure=True,
        )
        return response
    return await auth_provider.get_authorize_url(request, str(login_url))


@router.get("/auth/logout", name="logout")
@inject
async def logout(
    request: Request,
    response: Response,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    """
    Logout user by clearing session and removing cookie
    """
    if auth_provider is None:
        raise HTTPException(status_code=501, detail="Authentication not configured")

    # Revoke the access token at the OIDC provider before clearing it locally
    access_token = request.cookies.get(SESSION_COOKIE_NAME)
    if access_token:
        await auth_provider.revoke_token(access_token)

    base_url = request.base_url
    response = auth_provider.create_redirect_response(str(base_url))
    response.delete_cookie(SESSION_COOKIE_NAME)
    if hasattr(request, "session"):
        request.session.clear()

    return response
