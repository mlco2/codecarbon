from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import OrganizationCreate, TeamCreate, User, UserCreate
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService

USERS_ROUTER_TAGS = ["users"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post("/users/", tags=USERS_ROUTER_TAGS, status_code=status.HTTP_201_CREATED)
@inject
def create_user(
    user: UserCreate,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> User:
    return user_service.create_user(user)


@router.post(
    "/users/signup/", tags=USERS_ROUTER_TAGS, status_code=status.HTTP_201_CREATED
)
@inject
def sign_up(
    user: UserCreate,
    organization: OrganizationCreate,
    team: TeamCreate,
    signup_service: SignUpService = Depends(Provide[ServerContainer.sign_up]),
) -> User:
    return signup_service.sign_up(user, organization, team)


@router.get("/users/", tags=USERS_ROUTER_TAGS, status_code=status.HTTP_200_OK)
@inject
def list_users(
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return user_service.list_users()


@router.get("/users/{user_id}", tags=USERS_ROUTER_TAGS, status_code=status.HTTP_200_OK)
@inject
def get_user_by_id(
    user_id: str,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):

    return user_service.get_user_by_id(user_id)
