from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from carbonserver.api.schemas import Token, UserAuthenticate
from carbonserver.api.services.user_service import UserService

AUTHENTICATE_ROUTER_TAGS = ["/auth/"]

router = APIRouter()


@router.post(
    "/authenticate/", tags=AUTHENTICATE_ROUTER_TAGS, status_code=status.HTTP_200_OK
)
@inject
def auth_user(
    user: UserAuthenticate,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):

    verified_user = user_service.verify_user(user)
    if verified_user:
        return Token(access_token="a", token_type="access")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password!"
        )
