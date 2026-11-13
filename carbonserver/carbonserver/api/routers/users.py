import logging
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, Response, status

from carbonserver.api.routers.authenticate import (
    ID_TOKEN_COOKIE_NAME,
    SESSION_COOKIE_NAME,
)
from carbonserver.api.services.auth_providers.oidc_auth_provider import (
    OIDCAuthProvider,
)
from carbonserver.api.services.auth_service import (
    MandatoryUserWithAuthDependency,
    UserWithAuthDependency,
)
from carbonserver.api.services.user_service import UserService
from carbonserver.container import ServerContainer

LOGGER = logging.getLogger(__name__)

USERS_ROUTER_TAGS = ["Users"]

router = APIRouter()


@router.delete(
    "/users/me",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_current_user(
    request: Request,
    auth_user: UserWithAuthDependency = Depends(MandatoryUserWithAuthDependency),
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
    auth_provider: Optional[OIDCAuthProvider] = Depends(
        Provide[ServerContainer.auth_provider]
    ),
):
    """
    Permanently delete the signed-in user's CodeCarbon account.

    Organizations where the user is the only member are deleted with all their
    projects, experiments, runs, emissions and API tokens. Organizations shared
    with other members are kept; the user is only removed from them.

    The login itself lives at the OIDC provider and is not deleted here.
    Idempotent: a user already gone from the database gets 204 again.
    """
    if auth_user.db_user is not None:
        deleted_org_ids = user_service.delete_user(auth_user.db_user.id)
        LOGGER.info(
            "Deleted user %s and %d organization(s)",
            auth_user.db_user.id,
            len(deleted_org_ids),
        )

    access_token = request.cookies.get(SESSION_COOKIE_NAME)
    if access_token and auth_provider is not None:
        await auth_provider.revoke_token(access_token)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.delete_cookie(ID_TOKEN_COOKIE_NAME)
    if "session" in request.scope:
        request.session.clear()
    return response
