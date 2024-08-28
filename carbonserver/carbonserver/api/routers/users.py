from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import User
from carbonserver.api.services.user_service import UserService

USERS_ROUTER_TAGS = ["Users"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.get(
    "/users",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[User],
)
@inject
def list_users(
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> List[User]:
    return user_service.list_users()


@router.get(
    "/users/{user_id}",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=User,
)
@inject
def get_user_by_id(
    user_id: str,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> User:
    return user_service.get_user_by_id(user_id)
