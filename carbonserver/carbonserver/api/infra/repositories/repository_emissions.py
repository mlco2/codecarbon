from contextlib import AbstractContextManager
from typing import List
from uuid import uuid4

from dependency_injector.providers import Callable

from carbonserver.api import schemas
from carbonserver.api.domain.emissions import Emissions
from carbonserver.api.infra.database import sql_models

"""
The emissions are stored in the database by this repository class.
The emission repository is implemented to facilitate tests & the switch of database backend.
It relies on an abstract repository which exposes an interface of signatures shared by all repository implementations.

"""


class SqlAlchemyRepository(Emissions):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_emission(self, emission: schemas.EmissionCreate):
        """Save an emission to the database.

        :emission: An Emission in pyDantic BaseModel format.
        """
        with self.session_factory() as session:
            db_emission = sql_models.Emission(
                id=uuid4(),
                timestamp=emission.timestamp,
                duration=emission.duration,
                emissions_sum=emission.emissions_sum,
                emissions_rate=emission.emissions_rate,
                cpu_power=emission.cpu_power,
                gpu_power=emission.gpu_power,
                ram_power=emission.ram_power,
                cpu_energy=emission.cpu_energy,
                gpu_energy=emission.gpu_energy,
                ram_energy=emission.ram_energy,
                energy_consumed=emission.energy_consumed,
                run_id=emission.run_id,
            )
            session.add(db_emission)
            session.commit()
            return db_emission.id

    def get_one_emission(self, emission_id) -> schemas.Emission:
        """Find the emission in database and return it

        :emission_id: The id of the emission to retreive.
        :returns: An Emission in pyDantic BaseModel format.
        :rtype: schemas.Emission
        """
        with self.session_factory() as session:
            e = (
                session.query(sql_models.Emission)
                .filter(sql_models.Emission.id == emission_id)
                .first()
            )
            if e is None:
                return None
            else:
                return self.map_sql_to_schema(e)

    def get_emissions_from_run(self, run_id) -> List[schemas.Emission]:
        """Find the emissions from an run in database and return it

        :run_id: The id of the run to retreive emissions from.
        :returns: An Emission in pyDantic BaseModel format.
        :rtype: List[schemas.Emission]
        """
        with self.session_factory() as session:

            res = session.query(sql_models.Emission).filter(
                sql_models.Emission.run_id == run_id
            )
            if res.first() is None:
                return []
            else:
                emissions = []
                for e in res:
                    emission = self.map_sql_to_schema(e)
                    emissions.append(emission)
                return emissions

    @staticmethod
    def map_sql_to_schema(emission: sql_models.Emission) -> schemas.Emission:
        """Convert a models.Emission to a schemas.Emission

        :emission: An Emission in SQLAlchemy format.
        :returns: An Emission in pyDantic BaseModel format.
        :rtype: schemas.Emission
        """
        return schemas.Emission(
            id=emission.id,
            timestamp=emission.timestamp,
            duration=emission.duration,
            emissions_sum=emission.emissions_sum,
            emissions_rate=emission.emissions_rate,
            cpu_power=emission.cpu_power,
            gpu_power=emission.gpu_power,
            ram_power=emission.ram_power,
            cpu_energy=emission.cpu_energy,
            gpu_energy=emission.gpu_energy,
            ram_energy=emission.ram_energy,
            energy_consumed=emission.energy_consumed,
            run_id=emission.run_id,
        )
