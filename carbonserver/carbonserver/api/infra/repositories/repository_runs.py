import uuid
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable

from carbonserver.api import schemas
from carbonserver.api.domain.runs import Runs
from carbonserver.api.schemas import Run, RunCreate
from carbonserver.database.sql_models import Run as SqlModelRun

"""
Here there is all the methods to manipulate the run data
"""


class SqlAlchemyRepository(Runs):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_run(self, run: RunCreate) -> Run:
        """Save an Run to the database.
        :run: An Run in pyDantic BaseModel format.
        :returns: An Run in SQLAlchemy Model format.
        :rtype: models.Run
        """
        with self.session_factory() as session:
            db_run = SqlModelRun(
                id=uuid.uuid4(),
                timestamp=run.timestamp,
                experiment_id=run.experiment_id,
            )
            session.add(db_run)
            session.commit()
            session.refresh(db_run)
            return self.map_sql_to_schema(db_run)

        # db_run = sql_models.Run(
        #     timestamp=run.timestamp,
        #     experiment_id=run.experiment_id,
        # )
        # try:
        #     self.db.add(db_run)
        #     self.db.commit()
        #     self.db.refresh(db_run)
        #     return db_run
        # except exc.IntegrityError as e:
        #     # Sample error : sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "emissions" violates foreign key constraint "fk_emissions_runs"
        #     self.db.rollback()
        #     raise DBException(
        #         error=DBError(code=DBErrorEnum.INTEGRITY_ERROR, message=e.orig.args[0])
        #     )
        # except exc.DataError as e:
        #     self.db.rollback()
        #     # Sample error :  sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input syntax for type uuid: "5050f55-406d-495d-830e-4fd12c656bd1"
        #     raise DBException(

    def get_one_run(self, run_id):
        """Find the run in database and return it

        :run_id: The id of the run to retreive.
        :returns: An Run in pyDantic BaseModel format.
        :rtype: schemas.Run
        """
        with self.session_factory() as session:
            e = session.query(SqlModelRun).filter(SqlModelRun.id == run_id).first()
            if e is None:
                return None
            else:
                return self.map_sql_to_schema(e)

    def list_runs(self):
        with self.session_factory() as session:
            e = session.query(SqlModelRun)
            if e is None:
                return None
            else:
                runs: List[Run] = []
                for run in e:
                    runs.append(self.map_sql_to_schema(run))
                return runs

    @staticmethod
    def map_sql_to_schema(run: SqlModelRun) -> Run:
        """Convert a models.Run to a schemas.Run

        :emission: An Run in SQLAlchemy format.
        :returns: An Run in pyDantic BaseModel format.
        :rtype: schemas.Run
        """
        return Run(
            id=run.id,
            timestamp=run.timestamp,
            emission_id=run.emission_id,
            experiment_id=run.experiment_id,
        )


class InMemoryRepository(Runs):
    def __init__(self):
        self.runs: List = []
        self.id: int = 0

    def add_run(self, run: RunCreate):
        self.runs.append(
            SqlModelRun(
                id=self.id + 1,
                name=run.name,
                description=run.description,
                # organization_id=run.organization_id,
            )
        )

    def get_one_run(self, run_id) -> Run:
        first_run = self.runs[0]
        return Run(
            id=first_run.id,
            name=first_run.name,
            description=first_run.description,
            # organization_id=first_run.organization_id,
        )

    # def get_projects_from_run(self, run_id):
    # TODO : get Projects from Project id in database
    #    pass

    @staticmethod
    def get_db_to_class(self, run: SqlModelRun) -> Run:
        return schemas.Run(
            id=run.id,
            name=run.name,
            description=run.description,
            # organization_id=run.organization_id,
        )

    def list_run(self, run_name: str):
        runs = []
        for run in self.runs:
            runs.append(
                Run(
                    id=run.id,
                    name=run.name,
                    description=run.description,
                )
            )
        return runs
