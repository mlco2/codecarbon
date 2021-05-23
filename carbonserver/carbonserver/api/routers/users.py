from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from requests import Session

from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.errors import DBError, DBException
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import UserCreate
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


def create_user_db(db, user):
    repository_users = SqlAlchemyRepository(db)
    res = repository_users.create_user(user)
    if isinstance(res, DBError):
        raise DBException(error=res)
    else:
        return {"id": res.id}


# @router.get("/users/", tags=["users"], status_code=status)
def list_users(db: Session = Depends(get_db)):
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.list_users()
    return users


# @router.get("/user/", tags=["users"], status_code=200)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.get_user_by_id(user_id)
    return users
