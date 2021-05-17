import secrets
from typing import List
from carbonserver.api.domain.users import Users
from carbonserver.database import models
from carbonserver.api import schemas

from sqlalchemy.orm import Session


class SqlAlchemyRepository(Users):
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: schemas.UserCreate):
        db_user = models.User(
            user_id=user.name,
            name=user.name,
            email=user.email,
            hashed_password=user.password,
            api_key=_api_key_generator(),
            is_active=True,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user_by_id(self, user_id):
        """Find an user in database and return it

        :user_id: The id of the user to retrieve.
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        e = self.db.query(models.User).filter(models.User.id == user_id).first()
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def list_users(self):
        e = self.db.query(models.User)
        if e is None:
            return None
        else:
            users = []
            for user in e:
                users.append(self.get_db_to_class(user))
            return users

    @staticmethod
    def get_db_to_class(user: models.User) -> schemas.User:
        return schemas.User(
            id=user.user_id,
            name=user.name,
            email=user.email,
            password=user.password,
            api_key=user.api_key,
            is_active=user.is_active,
        )


class InMemoryRepository(Users):
    def __init__(self):
        self.users: List[Users] = []
        self.id: int = 0
        self.inactive_users: List = []

    def create_user(self, user: schemas.UserCreate) -> models.User:
        self.id += 1
        self.users.append(
            models.User(
                user_id=self.id,
                name=user.name,
                email=user.email,
                password=user.password,
                api_key=_api_key_generator(),
                is_active=True,
            )
        )
        return self.users[self.id - 1]

    def get_user_by_id(self, user_id: int):
        user = [user for user in self.users if user.user_id == user_id][0]
        return user

    def list_users(self):
        return self.users

    @staticmethod
    def get_db_to_class(user: models.User) -> schemas.User:
        return schemas.User(
            id=user.user_id,
            name=user.name,
            email=user.email,
            password=user.password,
            api_key=user.api_key,
            is_active=user.is_active,
        )


def _api_key_generator():
    generated_key = secrets.token_urlsafe(16)
    return generated_key
