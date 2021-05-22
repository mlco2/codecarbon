from fastapi import APIRouter, Depends
from requests import Session

from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.errors import DBError, DBException
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import UserCreate

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put("/users/", tags=["users"], status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user = 1
    return create_user_db(db, user)


def create_user_db(db, user):
    repository_users = SqlAlchemyRepository(db)
    res = repository_users.create_user(user)
    if isinstance(res, DBError):
        raise DBException(error=res)
    else:
        return {"id": res.id}


@router.get("/users/", tags=["users"], status_code=200)
def list_users(db: Session = Depends(get_db)):
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.list_users()
    return users


@router.get("/user/", tags=["users"], status_code=200)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    repository_users = SqlAlchemyRepository(db)
    users = repository_users.get_user_by_id(user_id)
    return users
