from typing import List

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import User, UserAutoCreate


class UserService:
    def __init__(self, user_repository: SqlAlchemyRepository) -> None:
        self._repository: SqlAlchemyRepository = user_repository

    def create_user(self, user: UserAutoCreate) -> User:
        created_user: User = self._repository.create_user(user)
        return created_user

    def create_user_by_id(self, user: UserAutoCreate) -> User:
        print("userservice", user)
        created_user: User = self._repository.create_user(user)
        return created_user

    def get_user_by_id(self, user_id: str) -> User:
        user: User = self._repository.get_user_by_id(user_id)
        return user

    def list_users(self) -> List[User]:
        users_list = self._repository.list_users()
        return users_list

    def add_organization(self, user: User, organisation_id: str):
        return self._repository.add_organisation(user, organisation_id)
