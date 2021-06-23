from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.projects import Projects
from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.api.infra.database import sql_models

"""
Here there is all the method to manipulate the project data
"""


class SqlAlchemyRepository(Projects):
    def __init__(self, db: Session):
        self.db = db

    def add_project(self, project: schemas.ProjectCreate):
        # TODO : save Project in database and get her ID
        db_project = sql_models.Project(
            name=project.name,
            description=project.description,
            team_id=project.team_id,
        )

        try:
            self.db.add(db_project)
            self.db.commit()
            self.db.refresh(db_project)
            return db_project
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

    def get_one_project(self, project_id):
        """Find the projet in database and return it

        :project_id: The id of the experiment to retreive.
        :returns: An Project in pyDantic BaseModel format.
        :rtype: schemas.Project
        """
        e = (
            self.db.query(sql_models.Project)
            .filter(sql_models.Project.id == project_id)
            .first()
        )
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

        # TODO : find the Project in database and return it
        # pass

    @staticmethod
    def get_db_to_class(project: sql_models.Project) -> schemas.Project:
        """Convert a models.Project to a schemas.Project

        :project: An Project in SQLAlchemy format.
        :returns: An Project in pyDantic BaseModel format.
        :rtype: schemas.Project
        """
        return schemas.Project(
            id=project.id,
            name=project.name,
            description=project.description,
            team_id=project.team_id,
        )


class InMemoryRepository(Projects):
    def __init__(self):
        self.projects: List = []
        self.id: int = 0

    def add_project(self, project: schemas.ProjectCreate):
        self.projects.append(
            sql_models.Project(
                id=self.id + 1,
                name=project.name,
                description=project.description,
                team_id=project.team_id,
            )
        )

    def get_one_project(self, project_id) -> schemas.Project:
        first_project = self.projects[0]
        return schemas.Project(
            id=first_project.id,
            name=first_project.name,
            description=first_project.description,
            team_id=first_project.team_id,
        )

    @staticmethod
    def get_db_to_class(project: sql_models.Project) -> schemas.Project:
        return schemas.Project(
            id=project.id,
            name=project.name,
            description=project.description,
            team_id=project.team_id,
        )
