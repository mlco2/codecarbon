from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.organizations import Organizations
from carbonserver.api.errors import DBError, DBErrorEnum, DBException
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

        try:
            self.db.add(db_organization)
            self.db.commit()
            self.db.refresh(db_organization)
            return db_organization
        except exc.IntegrityError as e:
            # Sample error : sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "emissions" violates foreign key constraint "fk_emissions_runs"
            self.db.rollback()
            raise DBException(
                error=DBError(code=DBErrorEnum.INTEGRITY_ERROR, message=e.orig.args[0])
            )
        except exc.DataError as e:
            self.db.rollback()
            # Sample error :  sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input syntax for type uuid: "5050f55-406d-495d-830e-4fd12c656bd1"
            raise DBException(
                error=DBError(code=DBErrorEnum.DATA_ERROR, message=e.orig.args[0])
            )
        except exc.ProgrammingError as e:
            # sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) can't adapt type 'SecretStr'
            self.db.rollback()
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.PROGRAMMING_ERROR, message=e.orig.args[0]
                )
            )

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
