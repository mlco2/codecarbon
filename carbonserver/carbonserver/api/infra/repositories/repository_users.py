import hashlib
import os
from _ast import List

from pydantic import SecretStr

from carbonserver.api import schemas
from carbonserver.api.domain.user import User
from carbonserver.database import models


class InMemoryRepository(User):
    def __init__(self):
        self.users: List[User] = []
        self.id: int = 0
        self.inactive_users: List = []

    def create_user(self, user: schemas.UserCreate) -> str:
        self.id += 1
        self.users.append(
            models.User(
                user_id=self.id,
                name=user.name,
                email=user.email,
                hashed_password=hash_password(user.password),
                api_key=user.api_key,
                is_active=user.is_active,
            )
        )
        return self.users[self.id - 1]

    def list_users(self):
        return self.users

    def get_user_by_id(self, user_id: int):
        pass


def hash_password(password: str) -> SecretStr:
    salt = random_generator()  # Extract random generation to make it easier to mock
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    hashed_password = salt + key

    return hashed_password


def random_generator():
    return os.urandom(32)
