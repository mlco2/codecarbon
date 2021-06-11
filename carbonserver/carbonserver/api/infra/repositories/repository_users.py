import uuid
from contextlib import AbstractContextManager
from typing import Callable, List

from carbonserver.api.domain.users import Users
from carbonserver.api.infra.api_key_service import generate_api_key
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
                api_key=generate_api_key(),
                is_active=True,
                teams=[],
                organizations=[],
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return self.map_sql_to_schema(db_user)

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
                print("printing user")
                print(e)
                return e  # self.map_sql_to_schema(e)

    def list_users(self) -> List[User]:
        with self.session_factory() as session:
            e = session.query(SqlModelUser)
            if e is None:
                return None
            else:
                users: List[User] = []
                for user in e:
                    users.append(self.map_sql_to_schema(user))
                return users

    def add_user_to_org(self, user: User, organization_id: str):
        with self.session_factory() as session:
            e = (
                session.query(SqlModelUser)
                .filter(SqlModelUser.id == user.id)
                .update(
                    {
                        SqlModelUser.organizations: user.organizations.append(
                            organization_id
                        )
                    },
                    synchronize_session=False,
                )
            )
            print(e)
            return e

    def add_user_to_team(self, user: User, team_id: str):
        with self.session_factory() as session:
            return (
                session.query(SqlModelUser)
                .filter(SqlModelUser.id == user.id)
                .update(
                    {SqlModelUser.organizations: user.teams.append(team_id)},
                    synchronize_session=False,
                )
            )

    @staticmethod
    def map_sql_to_schema(sql_user: SqlModelUser) -> User:
        """Sql To Pydantic Mapper

        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        print("I PRINT USER")
        print(sql_user)
        return User(
            id=str(sql_user.id),
            name=sql_user.name,
            email=sql_user.email,
            password=sql_user.hashed_password,
            api_key=sql_user.api_key,
            is_active=sql_user.is_active,
            teams=sql_user.teams,
            organizations=sql_user.organizations,
        )
