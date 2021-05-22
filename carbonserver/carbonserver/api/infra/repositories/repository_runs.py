from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.runs import Runs
from carbonserver.api.errors import DBErrorEnum, DBError, DBException
from carbonserver.database import models

"""
Here there is all the method to manipulate the experiment data
"""


class SqlAlchemyRepository(Runs):
    def __init__(self, db: Session):
        self.db = db

    def add_run(self, run: schemas.RunCreate) -> models.Run:
        """Save an Run to the database.
        :run: An Run in pyDantic BaseModel format.
        :returns: An Run in SQLAlchemy Model format.
        :rtype: models.Run
        """
        db_run = models.Run(
            timestamp=run.timestamp,
            experiment_id=run.experiment_id,
        )
        try:
            self.db.add(db_run)
            self.db.commit()
            self.db.refresh(db_run)
            return db_run
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

    @staticmethod
    def get_db_to_class(self, run: models.Run) -> schemas.Run:
        """Convert a models.Run to a schemas.Run

        :emission: An Run in SQLAlchemy format.
        :returns: An Run in pyDantic BaseModel format.
        :rtype: schemas.Run
        """
        return schemas.Run(
            id=run.id,
            timestamp=run.timestamp,
            emission_id=run.emission_id,
            experiment_id=run.experiment_id,
        )
