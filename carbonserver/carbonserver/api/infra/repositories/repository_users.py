from contextlib import AbstractContextManager
from typing import Callable, List
from uuid import UUID

from fastapi import HTTPException

from carbonserver.api.domain.users import Users
from carbonserver.api.infra.database.sql_models import Membership as SqlModelMembership
from carbonserver.api.infra.database.sql_models import Project as SqlModelProject
from carbonserver.api.infra.database.sql_models import User as SqlModelUser
from carbonserver.api.schemas import User, UserAutoCreate


class SqlAlchemyRepository(Users):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def create_user(self, user: UserAutoCreate) -> User:
        """Creates a user in the database
        :returns: A User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        with self.session_factory() as session:
            db_user = SqlModelUser(
                id=user.id,
                name=user.name,
                email=user.email,
                is_active=True,
                organizations=[],
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return self.map_sql_to_schema(db_user)

    def get_user_by_id(self, user_id: UUID) -> User:
        """Find an user in database and retrieves it

        :user_id: The id of the user to retrieve.
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        with self.session_factory() as session:
            e = session.query(SqlModelUser).filter(SqlModelUser.id == user_id).first()
            if e is None:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            return self.map_sql_to_schema(e)

    def list_users(self) -> List[User]:
        with self.session_factory() as session:
            e = session.query(SqlModelUser)
            if e is None:
                return None
            users: List[User] = []
            for user in e:
                users.append(self.map_sql_to_schema(user))
            return users

    def subscribe_user_to_org(
        self,
        user: User,
        organization_id: UUID,
    ) -> None:
        with self.session_factory() as session:
            e = (
                session.query(SqlModelMembership)
                .filter(SqlModelMembership.user_id == user.id)
                .first()
            )
            if e is not None:
                return

            db_membership = SqlModelMembership(
                user_id=user.id,
                organization_id=organization_id,
                is_admin=True,
            )
            session.add(db_membership)
            session.commit()
            return self.map_sql_to_schema(e)

    def is_user_authorized_on_project(self, project_id, user_id: UUID):
        with self.session_factory() as session:
            project_subquery = (
                session.query(SqlModelProject)
                .where(SqlModelProject.id == project_id)
                .first()
            )
            user_authorized_on_project = (
                session.query(SqlModelUser)
                .where(SqlModelUser.id == user_id)
                .filter(
                    SqlModelUser.organizations.any(
                        str(project_subquery.organization_id)
                    )
                )
                .all()
            )
            print(user_authorized_on_project)
            return bool(user_authorized_on_project)

    @staticmethod
    def map_sql_to_schema(sql_user: SqlModelUser) -> User:
        """Sql To Pydantic Mapper

        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        return User(
            id=sql_user.id,
            name=sql_user.name,
            email=sql_user.email,
            is_active=sql_user.is_active,
            organizations=[m.organization_id for m in sql_user.organizations],
        )
