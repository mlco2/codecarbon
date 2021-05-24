import secrets
from typing import List

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import User, UserCreate


class UserService:
    def __init__(self, user_repository: SqlAlchemyRepository) -> None:
        self._repository: SqlAlchemyRepository = user_repository

    def create_user(self, user: UserCreate) -> User:
        created_user = self._repository.create_user(user)

        return created_user

    def get_user_by_id(self, user_id: str) -> User:
        created_user: User = self._repository.get_user_by_id(user_id)

        return created_user

    def list_users(self) -> List[User]:
        users_list = self._repository.list_users()

        return users_list

    @staticmethod
    def api_key_generator():
        yield secrets.token_urlsafe(16)
