from typing import List

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import User, UserAuthenticate, UserCreate


class UserService:
    def __init__(self, user_repository: SqlAlchemyRepository) -> None:
        self._repository: SqlAlchemyRepository = user_repository

    def create_user(self, user: UserCreate) -> User:
        created_user: User = self._repository.create_user(user)

        return created_user

    def get_user_by_id(self, user_id: str) -> User:
        user: User = self._repository.get_user_by_id(user_id)
        return user
