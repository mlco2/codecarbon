import secrets
import uuid
from contextlib import AbstractContextManager
from typing import Callable, List


from carbonserver.api.domain.users import Users
from carbonserver.api.schemas import User, UserCreate
from carbonserver.database.sql_models import User as SqlModelUser


class SqlAlchemyRepository(Users):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def create_user(self, user: UserCreate) -> User:
        """Creates an user in the database
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        with self.session_factory() as session:
            db_user = SqlModelUser(
                id=uuid.uuid4(),
                name=user.name,
                email=user.email,
                hashed_password=user.password,
                api_key=self.api_key_generator(),
                is_active=True,
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return self.get_db_to_class(db_user)

    def get_user_by_id(self, user_id: str) -> User:
        """Find an user in database and retrieves it

        :user_id: The id of the user to retrieve.
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        with self.session_factory() as session:
            e = session.query(SqlModelUser).filter(SqlModelUser.id == user_id).first()
            # noinspection PyPackageRequirements
            if e is None:
                return None
            else:
                return self.get_db_to_class(e)

    def list_users(self) -> List[User]:
        with self.session_factory() as session:
            e = session.query(SqlModelUser)
            if e is None:
                return None
            else:
                users = []
                for user in e:
                    users.append(self.get_db_to_class(user))
                return users

    @staticmethod
    def get_db_to_class(sql_user: SqlModelUser) -> User:
        """Sql To Pydantic Mapper

        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        return User(
            id=str(sql_user.id),
            name=sql_user.name,
            email=sql_user.email,
            password=sql_user.hashed_password,
            api_key=sql_user.api_key,
            is_active=sql_user.is_active,
        )

    @staticmethod
    def api_key_generator():
        return secrets.token_urlsafe(16)


class InMemoryRepository(Users):
    def __init__(self):
        self.users: List[Users] = []
        self.id: int = 0
        self.inactive_users: List = []

    def create_user(self, user: UserCreate) -> SqlModelUser:
        self.id += 1
        self.users.append(
            SqlModelUser(
                id=self.id,
                name=user.name,
                email=user.email,
                hashed_password=user.password,
                api_key=SqlAlchemyRepository.api_key_generator(),
                is_active=True,
            )
        )
        return self.users[self.id - 1]

    def get_user_by_id(self, user_id: int):
        user = [user for user in self.users if user.id == user_id][0]
        return user

    def list_users(self):
        return self.users

    @staticmethod
    def get_db_to_class(user: SqlModelUser) -> User:
        return User(
            id=user.user_id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            api_key=user.api_key,
            is_active=user.is_active,
        )
