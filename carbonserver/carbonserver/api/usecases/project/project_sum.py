from typing import List

from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import ProjectReport


class ProjectSumsUsecase:
    def __init__(self, project_repository: SqlAlchemyRepository) -> None:
        self._project_repository = project_repository

    def compute_detailed_sum(
        self, project_id: str, start_date, end_date
    ) -> List[ProjectReport]:
        sums = self._project_repository.get_project_detailed_sums(
            project_id,
            start_date,
            end_date,
        )
        return sums
