from contextlib import AbstractContextManager
from typing import Callable, List
from uuid import UUID, uuid4

import bcrypt
from fastapi import HTTPException
from sqlalchemy import update

from carbonserver.api.domain.users import Users
from carbonserver.api.infra.api_key_service import generate_api_key
from carbonserver.api.infra.database.sql_models import User as SqlModelUser
from carbonserver.api.infra.database.sql_models import Project as SqlModelProject
from carbonserver.api.infra.database.sql_models import Organization as SqlModelOrganization
from carbonserver.api.schemas import User, UserAuthenticate, UserAutoCreate, UserCreate


class SqlAlchemyRepository(Users):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def create_user(self, user: UserAutoCreate) -> User:
        """Creates a user in the database
        :returns: A User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        with self.session_factory() as session:
            db_user = (
                SqlModelUser(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    api_key=generate_api_key(),
                    is_active=True,
                    organizations=[],
                )
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

    def is_user_authorized_on_project(self, project_id, user_id: UUID):
        with self.session_factory() as session:
            project_subquery = session.query(SqlModelProject).where(SqlModelProject.id == project_id).subquery()
            user_authorized_on_project = session.query(SqlModelUser).where(SqlModelUser.id == user_id).filter(
                SqlModelUser.organizations.contains(project_subquery.c.id)).first()
            return bool(user_authorized_on_project)

    def subscribe_user_to_org(
        self,
        user: User,
        organization_id: UUID,
    ) -> User:
        with self.session_factory() as session:
            user.organizations = []

            if organization_id in user.organizations:
                return user

            stmt = (
                update(SqlModelUser)
                .where(SqlModelUser.id == user.id)
                .values(
                    {
                        "organizations": [*user.organizations, organization_id],
                    }
                )
                .returning(SqlModelUser)
            )
            e = session.execute(stmt).one()
            session.commit()
            return self.map_sql_to_schema(e)

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
            api_key=sql_user.api_key,
            is_active=sql_user.is_active,
            organizations=sql_user.organizations,
        )
