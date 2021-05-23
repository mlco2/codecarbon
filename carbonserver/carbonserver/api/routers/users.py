from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from requests import Session

from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import OrganizationCreate, TeamCreate, UserCreate
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post("/users/", tags=["users"], status_code=status.HTTP_201_CREATED)
@inject
def create_user(
    user: UserCreate,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return user_service.create_user(user)


@router.post("/users/signup/", tags=["users"], status_code=status.HTTP_201_CREATED)
@inject
def sign_up(
    user: UserCreate,
    organization: OrganizationCreate,
    team: TeamCreate,
    signup_service: SignUpService = Depends(Provide[ServerContainer.user_service]),
):
    return signup_service.sign_up(user, organization, team)


@router.get("/users/", tags=["users"], status_code=status.HTTP_200_OK)
@inject
def list_users(
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return user_service.list_users()


# @router.get("/user/", tags=["users"], status_code=200)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.get_user_by_id(user_id)
    return users
