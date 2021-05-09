import secrets
from typing import List


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
                password= user.password,
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


def _api_key_generator():
    generated_key = secrets.token_urlsafe(16)
    return generated_key
