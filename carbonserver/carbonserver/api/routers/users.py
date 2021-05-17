from fastapi import APIRouter, Depends

from carbonserver.api.dependencies import get_token_header
from carbonserver.database.schemas import UserCreate
from carbonserver.api.infra.repositories.repository_users import InMemoryRepository

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)

repository_users = InMemoryRepository()


@router.put("/users/", tags=["users"], status_code=201)
def create_user(user: UserCreate):

    created_user = repository_users.create_user(user)
    return created_user


@router.get("/users/", tags=["users"], status_code=200)
def list_users():

    users = repository_users.list_users()
    return users


@router.get("/user/", tags=["users"], status_code=200)
def get_user_by_id(user_id: int):

    users = repository_users.get_user_by_id(user_id)
    return users
