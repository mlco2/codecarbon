import abc
from typing import List
from uuid import UUID

from carbonserver.api.schemas import User, UserAutoCreate


class Users(abc.ABC):
    @abc.abstractmethod
    def create_user(self, user: UserAutoCreate) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    def list_users(self) -> List[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_user(self, user_id: UUID) -> List[UUID]:
        raise NotImplementedError
