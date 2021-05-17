from fastapi import APIRouter, Depends
from requests import Session

from carbonserver.api.dependencies import get_token_header, get_db
from carbonserver.api.schemas import UserCreate
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put("/users/", tags=["users"], status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    repository_users = SqlAlchemyRepository(db)
    created_user = repository_users.create_user(user)
    return created_user


@router.get("/users/", tags=["users"], status_code=200)
def list_users():
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.list_users()
    return users


@router.get("/user/", tags=["users"], status_code=200)
def get_user_by_id(user_id: int):
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.get_user_by_id(user_id)
    return users
