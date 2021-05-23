import abc
from typing import List

from carbonserver.api.schemas import User, UserCreate


class Users(abc.ABC):
    @abc.abstractmethod
    def create_user(self, user: UserCreate) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    def list_users(self) -> List[User]:
        raise NotImplementedError
