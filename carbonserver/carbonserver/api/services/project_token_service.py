from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository as ProjectTokensSqlRepository,
)
from carbonserver.api.schemas import ProjectTokenCreate


class ProjectTokenService:
    def __init__(self, project_token_repository: ProjectTokensSqlRepository):
        self._repository = project_token_repository

    def add_project_token(self, project_id, project_token: ProjectTokenCreate):
        return self._repository.add_project_token(project_id, project_token)

    def delete_project_token(self, project_id, token_id):
        return self._repository.delete_project_token(project_id, token_id)

    def list_tokens_from_project(self, project_id):
        return self._repository.list_project_tokens(project_id)
