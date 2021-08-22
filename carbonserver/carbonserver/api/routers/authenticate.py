from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from carbonserver.api.schemas import Token, UserAuthenticate
from carbonserver.api.services.authentication.authentication_service import (
    AuthenticationService,
)
from carbonserver.api.services.user_service import UserService

AUTHENTICATE_ROUTER_TAGS = ["Authenticate"]

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
        return Token(access_token="a", token_type="id")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password or email!",
        )


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
    "/login_package",
    tags=AUTHENTICATE_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Token,
)
@inject
def login_package(
    client_id: str,
    client_secret: str,
    authentication_service: AuthenticationService = Depends(
        Provide[ServerContainer.authentication_service]
    ),
) -> Token:
    access_token = authentication_service.login_with_client_credentials(
        client_id, client_secret
    )
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
