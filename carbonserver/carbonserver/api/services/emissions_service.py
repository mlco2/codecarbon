from typing import List
from uuid import UUID

from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository as EmissionSqlRepository,
)
from carbonserver.api.schemas import Emission, EmissionCreate


class EmissionService:
    def __init__(self, emission_repository: EmissionSqlRepository):
        self._repository = emission_repository

    def add_emission(self, emission: EmissionCreate) -> UUID:
        emission = self._repository.add_emission(emission)
        return emission

    def get_one_emission(self, emission_id) -> Emission:
        emission = self._repository.get_one_emission(emission_id)
        return emission

    def get_emissions_from_run(self, run_id) -> List[Emission]:
        emissions = self._repository.get_emissions_from_run(run_id)
        return emissions
