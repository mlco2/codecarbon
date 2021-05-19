from typing import List

from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.organizations import Organizations
from carbonserver.database import models

"""
Here there is all the method to manipulate the organization data
"""


class SqlAlchemyRepository(Organizations):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def get_db_to_class(organization: models.Organization) -> schemas.Organization:
        return schemas.Organization(
            id=organization.id,
            name=organization.name,
            description=organization.description,
        )

    def add_organization(self, organization: schemas.OrganizationCreate):
        # TODO : save Organization in database and get her ID
        db_organization = models.Organization(
            name=organization.name, description=organization.description
        )
        self.db.add(db_organization)
        self.db.commit()
        self.db.refresh(db_organization)
        return db_organization

    def get_one_organization(self, organization_id: str):
        """Find the organization in database and return it

        :organization_id: The id of the organization to retreive.
        :returns: An Organization in pyDantic BaseModel format.
        :rtype: schemas.Organization
        """
        e = (
            self.db.query(models.Organization)
            .filter(models.Organization.id == organization_id)
            .first()
        )
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def get_team_from_organizations(self, organization_name: str):
        # TODO : get Organization from team id in database
        pass


class InMemoryRepository(Organizations):
    def __init__(self):
        self.organizations: List = []
        self.id: int = 0

    def get_db_to_class(
        self, organization: models.Organization
    ) -> schemas.Organization:
        return schemas.Organization(
            id=organization.id,
            name=organization.name,
            description=organization.description,
        )

    def add_organization(self, organization: schemas.OrganizationCreate):
        self.organizations.append(
            models.Experiment(
                id=self.id + 1,
                name=organization.name,
                description=organization.description,
            )
        )

    def get_one_organization(self, organization_name: str) -> schemas.Organization:
        organization = self.organizations[0]
        return schemas.Organization(
            id=organization.id,
            name=organization.name,
            description=organization.description,
        )

    def get_team_from_organizations(self, organization_name: str):
        organizations = []
        for organization in self.organizations:
            organizations.append(
                schemas.Organization(
                    id=organization.id,
                    name=organization.name,
                    description=organization.description,
                )
            )
        return organizations
