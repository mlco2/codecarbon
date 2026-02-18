from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from carbonserver.api.schemas import User
from carbonserver.api.services.user_service import UserService
from carbonserver.container import ServerContainer

USERS_ROUTER_TAGS = ["Users"]

router = APIRouter()


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
