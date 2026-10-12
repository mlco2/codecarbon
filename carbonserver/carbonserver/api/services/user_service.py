from typing import List
from uuid import UUID

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import User, UserAutoCreate


class UserService:
    def __init__(self, user_repository: SqlAlchemyRepository) -> None:
        self._repository: SqlAlchemyRepository = user_repository

    def create_user(self, user: UserAutoCreate) -> User:
        return self._repository.create_user(user)

    def create_user_by_id(self, user: UserAutoCreate) -> User:
        return self.create_user(user)

    def get_user_by_id(self, user_id: str) -> User:
        return self._repository.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> User:
        return self._repository.get_user_by_email(email)

    def list_users(self) -> List[User]:
        return self._repository.list_users()

    def add_organization(self, user: User, organization_id: UUID) -> None:
        return self._repository.subscribe_user_to_org(
            user=user,
            organization_id=organization_id,
            is_admin=False,
        )
