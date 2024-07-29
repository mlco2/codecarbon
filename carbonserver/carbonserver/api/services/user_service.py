from typing import List

from carbonserver.api.infra.repositories.users.sql_repository import SqlAlchemyRepository
from carbonserver.api.schemas import User, UserAutoCreate


class UserService:
    def __init__(self, user_repository: SqlAlchemyRepository) -> None:
        self._repository: SqlAlchemyRepository = user_repository

    def create_user(self, user: UserAutoCreate) -> User:
        created_user: User = self._repository.create_user(user)

        return created_user

    def get_user_by_id(self, user_id: str) -> User:
        user: User = self._repository.get_user_by_id(user_id)
        return user
