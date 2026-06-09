import abc
from typing import List
from uuid import UUID

from carbonserver.api import schemas


class Emissions(abc.ABC):
    @abc.abstractmethod
    def add_emission(self, emission: schemas.EmissionCreate) -> UUID:
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_emission(self, emission_id) -> schemas.Emission:
        raise NotImplementedError

    @abc.abstractmethod
    def get_emissions_from_run(self, run_id) -> List[schemas.Emission]:
        raise NotImplementedError
