from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from carbonserver.api.services.auth_service import MandatoryUserWithAuthDependency
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
    auth_user=Depends(MandatoryUserWithAuthDependency),
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> User:
    if auth_user.id != user_id and not auth_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user",
        )
    return user_service.get_user_by_id(user_id)