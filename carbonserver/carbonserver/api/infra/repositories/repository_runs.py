from carbonserver.api.domain.runs import Runs
from carbonserver.database import models
from carbonserver.api import schemas
from sqlalchemy.orm import Session

"""
Here there is all the method to manipulate the experiment data
"""


class SqlAlchemyRepository(Runs):
    def __init__(self, db: Session):
        self.db = db

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

    def add_run(self, run: schemas.RunCreate):
        """Save an Run to the database.
        :run: An Run in pyDantic BaseModel format.
        """
        db_run = models.Run(
            timestamp=run.timestamp,
            experiment_id=run.experiment_id,
        )
        self.db.add(db_run)
        self.db.commit()
