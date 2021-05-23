from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.teams import Teams
from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.database import sql_models

"""
Here there is all the method to manipulate the project data
"""


class SqlAlchemyRepository(Teams):
    def __init__(self, db: Session):
        self.db = db

    def add_team(self, team: schemas.TeamCreate):
        # TODO : save Team in database and get her ID
        db_team = sql_models.Team(
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )

        try:
            self.db.add(db_team)
            self.db.commit()
            self.db.refresh(db_team)
            return db_team
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

    def get_one_team(self, team_id):
        """Find the team in database and return it

        :team_id: The id of the team to retreive.
        :returns: An Team in pyDantic BaseModel format.
        :rtype: schemas.Team
        """
        e = self.db.query(sql_models.Team).filter(sql_models.Team.id == team_id).first()
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def get_projects_from_team(self, team_id):
        # TODO : get Projects from Project id in database
        pass

    @staticmethod
    def get_db_to_class(team: sql_models.Team) -> schemas.Team:
        return schemas.Team(
            id=team.id,
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )


class InMemoryRepository(Teams):
    def __init__(self):
        self.teams: List = []
        self.id: int = 0

    def add_team(self, team: schemas.TeamCreate):
        self.teams.append(
            sql_models.Team(
                id=self.id + 1,
                name=team.name,
                description=team.description,
                organization_id=team.organization_id,
            )
        )

    def get_one_team(self, team_id) -> schemas.Team:
        first_team = self.teams[0]
        return schemas.Team(
            id=first_team.id,
            name=first_team.name,
            description=first_team.description,
            organization_id=first_team.organization_id,
        )

    def get_projects_from_team(self, team_id):
        # TODO : get Projects from Project id in database
        pass

    @staticmethod
    def get_db_to_class(team: sql_models.Team) -> schemas.Team:
        return schemas.Team(
            id=team.id,
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )
