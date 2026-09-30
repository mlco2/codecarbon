import logging
from typing import Optional

from authlib.integrations.starlette_client import OAuthError
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, Response
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

LOGGER = logging.getLogger(__name__)
SESSION_COOKIE_NAME = "user_session"
# Raw id_token, kept only as the hint for provider-side logout.
ID_TOKEN_COOKIE_NAME = "user_id_token"


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


@router.get("/auth/login", name="login")
@inject
async def get_login(
    request: Request,
    code: Optional[str] = None,
    sign_up_service: SignUpService = Depends(Provide[ServerContainer.sign_up_service]),
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    """
    Log in and redirect to the frontend with an HTTP-only session cookie.
    """
    if auth_provider is None:
        return RedirectResponse(settings.default_redirect_url)
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

        base_url = request.base_url
        if settings.frontend_url != "":
            base_url = settings.frontend_url + "/"
        url = f"{base_url}home"
        response = auth_provider.create_redirect_response(url)

        # A Secure cookie is dropped outright over plain http, which is every
        # local dev session, so the requirement is relaxed there.
        cookie_options = {
            "httponly": True,
            "secure": settings.environment not in ("local", "develop"),
            "samesite": "lax",
        }
        response.set_cookie(
            SESSION_COOKIE_NAME, token["access_token"], **cookie_options
        )
        # Its own cookie rather than the session: the session is a signed
        # client-side cookie capped at ~4KB, and an id_token is large enough to
        # push it over and get it dropped silently.
        if isinstance(token.get("id_token"), str):
            response.set_cookie(
                ID_TOKEN_COOKIE_NAME, token["id_token"], **cookie_options
            )
        return response
    return await auth_provider.get_authorize_url(request, str(login_url))


@router.get("/auth/logout", name="logout")
@inject
async def logout(
    request: Request,
    response: Response,
    auth_user: UserWithAuthDependency = Depends(OptionalUserWithAuthDependency),
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    """
    Logout user by ending the provider's SSO session, clearing our own session
    and removing the cookie.
    """
    if auth_provider is None:
        return RedirectResponse(settings.default_redirect_url)

    # Revoke the access token at the OIDC provider before clearing it locally
    access_token = request.cookies.get(SESSION_COOKIE_NAME)
    if access_token:
        await auth_provider.revoke_token(access_token)

    id_token = request.cookies.get(ID_TOKEN_COOKIE_NAME)

    # Land the user back on the dashboard, not on the API host. The trailing
    # slash is deliberate: the provider matches this against the client's
    # registered post-logout URIs exactly.
    post_logout_url = (
        f"{settings.frontend_url.rstrip('/')}/"
        if settings.frontend_url
        else str(request.base_url)
    )
    redirect_url = await auth_provider.get_end_session_url(
        post_logout_url, id_token=id_token
    )

    response = auth_provider.create_redirect_response(redirect_url or post_logout_url)
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.delete_cookie(ID_TOKEN_COOKIE_NAME)
    if hasattr(request, "session"):
        request.session.clear()

    return response


@router.get("/auth/account", name="account")
@inject
async def account(
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    """
    Send the user to the provider's account console, which owns their email and
    password. The issuer lives in the server config only, so the frontend links
    here rather than needing the URL itself.
    """
    if auth_provider is None:
        return RedirectResponse(settings.default_redirect_url)
    return auth_provider.create_redirect_response(auth_provider.get_account_url())
