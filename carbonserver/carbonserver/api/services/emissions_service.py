from typing import List, Optional
from uuid import UUID

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository as EmissionSqlRepository,
)
from carbonserver.api.schemas import Emission, EmissionCreate, User
from carbonserver.api.services.auth_context import AuthContext


def _not_allowed() -> UserException:
    return UserException(
        NotAllowedError(
            code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
            message="Operation not authorized",
        )
    )


class EmissionService:
    def __init__(
        self,
        emission_repository: EmissionSqlRepository,
        auth_context: AuthContext,
    ):
        self._repository = emission_repository
        self._auth_context = auth_context

    def add_emission(self, emission: EmissionCreate) -> UUID:
        emission_id = self._repository.add_emission(emission)
        return emission_id

    def get_one_emission(
        self, emission_id, user: Optional[User] = None
    ) -> Emission:
        emission = self._repository.get_one_emission(emission_id)
        if not self._auth_context.can_read_run(emission.run_id, user):
            raise _not_allowed()
        return emission

    def get_emissions_from_run(
        self, run_id, user: Optional[User] = None
    ) -> List[Emission]:
        if not self._auth_context.can_read_run(run_id, user):
            raise _not_allowed()
        emissions = self._repository.get_emissions_from_run(run_id)
        return emissions
