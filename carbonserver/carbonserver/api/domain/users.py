import abc
from typing import List

from carbonserver.api.schemas import User


class Users(abc.ABC):
    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> User:
        raise NotImplementedError
