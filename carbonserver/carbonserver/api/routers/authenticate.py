from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.schemas import Token, UserAuthenticate
from carbonserver.api.services.authentication.authentication_service import (
    AuthenticationService,
)

AUTHENTICATE_ROUTER_TAGS = ["Authenticate"]

router = APIRouter()


@router.post(
    "/login",
    tags=AUTHENTICATE_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Token,
)
@inject
def login(
    user: UserAuthenticate,
    authentication_service: AuthenticationService = Depends(
        Provide[ServerContainer.authentication_service]
    ),
) -> Token:
    access_token = authentication_service.login(user)
    return access_token


@router.post(
    "/register_client",
    tags=AUTHENTICATE_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def register_client(
    client_id: str,
    client_secret: str,
    authentication_service: AuthenticationService = Depends(
        Provide[ServerContainer.authentication_service]
    ),
) -> Token:
    access_token = authentication_service.register_client(client_id, client_secret)
    return access_token
