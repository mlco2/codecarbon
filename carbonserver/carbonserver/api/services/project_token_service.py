from fastapi import HTTPException

from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository as ProjectTokensSqlRepository,
)
from carbonserver.api.schemas import AccessLevel, ProjectToken, ProjectTokenCreate


class ProjectTokenService:
    def __init__(self, project_token_repository: ProjectTokensSqlRepository):
        self._repository = project_token_repository

    def add_project_token(self, project_id, project_token: ProjectTokenCreate):
        return self._repository.add_project_token(project_id, project_token)

    def delete_project_token(self, project_id, token_id):
        return self._repository.delete_project_token(project_id, token_id)

    def list_tokens_from_project(self, project_id):
        return self._repository.list_project_tokens(project_id)

    def project_token_has_access_to_project_id(
        self, desired_access: int, project_id, project_token: str
    ):
        if not project_token:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to perform this action. Missing project token",
            )
        # Verify that the project token is valid and has access to do the action
        full_project_token = self._repository.get_project_token_by_project_id_and_token(
            project_id, project_token
        )
        self._has_access(desired_access, full_project_token)

    def project_token_has_access_to_experiment_id(
        self, desired_access: int, experiment_id, project_token: str
    ):
        """
        Check if the project token has access to the experiment_id with the desired_access.
        Example: desired_access = AccessLevel.READ.value but the project_token has AccessLevel.WRITE.value ==> has_access = False because WRITE access is not READ
        Example2: desired_access = AccessLevel.WRITE.value and the project_token has AccessLevel.READ_WRITE.value ==> has_access = TRUE because READ_WRITE access contains WRITE access
        """
        if not project_token:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to perform this action. Missing project token",
            )
        # Verify that the project token is valid and has access to do the action
        full_project_token = (
            self._repository.get_project_token_by_experiment_id_and_token(
                experiment_id, project_token
            )
        )
        self._has_access(desired_access, full_project_token)

    def project_token_has_access_to_run_id(
        self, desired_access: int, run_id, project_token: str
    ):
        if not project_token:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to perform this action. Missing project token",
            )
        # Verify that the project token is valid and has access to do the action
        full_project_token = self._repository.get_project_token_by_run_id_and_token(
            run_id, project_token
        )
        self._has_access(desired_access, full_project_token)

    def project_token_has_access_to_emission_id(
        self, desired_access: int, emission_id, project_token: str
    ):
        if not project_token:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to perform this action. Missing project token",
            )
        # Verify that the project token is valid and has access to do the action
        full_project_token = (
            self._repository.get_project_token_by_emission_id_and_token(
                emission_id, project_token
            )
        )
        self._has_access(desired_access, full_project_token)

    def _has_access(self, desired_access: int, full_project_token: ProjectToken):
        has_access = (
            desired_access == full_project_token.access
            or full_project_token.access == AccessLevel.READ_WRITE.value
        )
        if not has_access:
            raise HTTPException(
                status_code=403, detail="Not allowed to perform this action"
            )
