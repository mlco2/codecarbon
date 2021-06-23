from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.emissions import Emissions
from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.api.infra.database import sql_models

"""
The emissions are stored in the database by this repository class.
The emission repository is implemented to facilitate tests & the switch of database backend.
It relies on an abstract repository which exposes an interface of signatures shared by all repository implementations.

"""


class SqlAlchemyRepository(Emissions):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def get_db_to_class(emission: sql_models.Emission) -> schemas.Emission:
        """Convert a models.Emission to a schemas.Emission

        :emission: An Emission in SQLAlchemy format.
        :returns: An Emission in pyDantic BaseModel format.
        :rtype: schemas.Emission
        """
        return schemas.Emission(
            id=emission.id,
            timestamp=emission.timestamp,
            duration=emission.duration,
            emissions=emission.emissions,
            energy_consumed=emission.energy_consumed,
            run_id=emission.run_id,
        )

    def add_emission(self, emission: schemas.EmissionCreate):
        """Save an emission to the database.

        :emission: An Emission in pyDantic BaseModel format.
        """
        db_emission = sql_models.Emission(
            timestamp=emission.timestamp,
            duration=emission.duration,
            emissions=emission.emissions,
            energy_consumed=emission.energy_consumed,
            run_id=emission.run_id,
        )
        try:
            self.db.add(db_emission)
            self.db.commit()
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

    def get_one_emission(self, emission_id) -> schemas.Emission:
        """Find the emission in database and return it

        :emission_id: The id of the emission to retreive.
        :returns: An Emission in pyDantic BaseModel format.
        :rtype: schemas.Emission
        """
        e = (
            self.db.query(sql_models.Emission)
            .filter(sql_models.Emission.id == emission_id)
            .first()
        )
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def get_emissions_from_run(self, run_id) -> List[schemas.Emission]:
        """Find the emissions from an run in database and return it

        :run_id: The id of the run to retreive emissions from.
        :returns: An Emission in pyDantic BaseModel format.
        :rtype: List[schemas.Emission]
        """
        res = self.db.query(sql_models.Emission).filter(
            sql_models.Emission.run_id == run_id
        )
        if res.first() is None:
            return []
        else:
            # Convert the table of models.Emission to a table of schemas.Emission
            emissions = []
            for e in res:
                emission = self.get_db_to_class(e)
                emissions.append(emission)
            return emissions


class InMemoryRepository(Emissions):
    def __init__(self):
        self.emissions: List = []
        self.id: int = 0

    def add_emission(self, emission: schemas.EmissionCreate):
        self.emissions.append(
            sql_models.Emission(
                id=self.id + 1,
                timestamp=emission.timestamp,
                duration=emission.duration,
                emissions=emission.emissions,
                energy_consumed=emission.energy_consumed,
                run_id=emission.run_id,
            )
        )

    def get_one_emission(self, emission_id) -> schemas.Emission:
        first_emission = self.emissions[0]
        return schemas.Emission(
            id=first_emission.id,
            timestamp=first_emission.timestamp,
            duration=first_emission.duration,
            emissions=first_emission.emissions,
            energy_consumed=first_emission.energy_consumed,
            run_id=first_emission.run_id,
        )

    def get_emissions_from_run(self, run_id) -> List[schemas.Emission]:
        print(len(self.emissions))
        stored_emissions = [
            stored_emission
            for stored_emission in self.emissions
            if stored_emission.run_id == run_id
        ]
        emissions: List[schemas.Emission] = []
        for emission in stored_emissions:
            emissions.append(self.get_db_to_class(emission))
        return emissions

    @staticmethod
    def get_db_to_class(emission: sql_models.Emission) -> schemas.Emission:
        return schemas.Emission(
            id=emission.id,
            timestamp=emission.timestamp,
            duration=emission.duration,
            emissions=emission.emissions,
            energy_consumed=emission.energy_consumed,
            run_id=emission.run_id,
        )
