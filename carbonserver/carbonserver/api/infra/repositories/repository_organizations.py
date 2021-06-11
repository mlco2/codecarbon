import uuid
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable

from carbonserver.api.domain.organizations import Organizations
from carbonserver.api.infra.api_key_service import generate_api_key
from carbonserver.api.schemas import Organization, OrganizationCreate
from carbonserver.database.sql_models import Organization as SqlModelOrganization

"""
Here there is all the method to manipulate the organization data
"""


class SqlAlchemyRepository(Organizations):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_organization(self, organization: OrganizationCreate) -> Organization:

        with self.session_factory() as session:
            db_organization = SqlModelOrganization(
                id=uuid.uuid4(),
                name=organization.name,
                description=organization.description,
                api_key=generate_api_key(),
            )

            session.add(db_organization)
            session.commit()
            session.refresh(db_organization)
            return self.map_sql_to_schema(db_organization)

    def get_one_organization(self, organization_id: str) -> Organization:
        """Find the organization in database and return it

        :organization_id: The id of the organization to retreive.
        :returns: An Organization in pyDantic BaseModel format.
        :rtype: schemas.Organization
        """
        with self.session_factory() as session:
            e = (
                session.query(SqlModelOrganization)
                .filter(SqlModelOrganization.id == organization_id)
                .first()
            )
            if e is None:
                return None
            else:
                return self.map_sql_to_schema(e)

    def list_organization(self):
        with self.session_factory() as session:
            e = session.query(SqlModelOrganization)
            if e is None:
                return None
            else:
                orgs: List[Organization] = []
                for org in e:
                    orgs.append(self.map_sql_to_schema(org))
                return orgs

    def is_api_key_valid(self, organization_id: str, api_key: str):
        with self.session_factory() as session:
            e = (
                session.query(SqlModelOrganization)
                .filter(SqlModelOrganization.id == organization_id)
                .filter(SqlModelOrganization.api_key == api_key)
                .first()
            )
            if e is None:
                return False
            else:
                return True

    @staticmethod
    def map_sql_to_schema(organization: SqlModelOrganization) -> Organization:
        return Organization(
            id=organization.id,
            name=organization.name,
            description=organization.description,
            api_key=organization.api_key,
        )
