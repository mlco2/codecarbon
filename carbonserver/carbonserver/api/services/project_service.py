from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectSqlRepository,
)
from carbonserver.api.schemas import ProjectCreate


class ProjectService:
    def __init__(self, project_repository: ProjectSqlRepository):
        self._repository = project_repository

    def add_project(self, project: ProjectCreate):
        return self._repository.add_project(project)

    def get_one_project(self, project_id):
        return self._repository.get_one_project(project_id)

    # TODO: DO a version of this method but that returns a list of projects of an organization
    # def list_projects_from_team(self, team_id: str):
    #     return self._repository.get_projects_from_team(team_id)
