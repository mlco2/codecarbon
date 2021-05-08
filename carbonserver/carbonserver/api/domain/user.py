import abc

from carbonserver.api import schemas


class User(abc.ABC):
    @abc.abstractmethod
    def create_user(self, user: schemas.UserCreate):
        pass

    @abc.abstractmethod
    def list_users(self):
        pass

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int):
        pass
