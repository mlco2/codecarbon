class AuthContext:

    def __init__(self, user_repository, token_repository):
        self._user_repository = user_repository
        self._token_repository = token_repository

    def isOperationAuthorizedOnOrg(self, organization_id, user):
        return self._user_repository.is_user_in_organization(
            organization_id=organization_id, user=user
        )

    def isOperationAuthorizedOnProject(self, project_id, user):
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)

    def is_admin_on_project(self, project_id, user):
        pass

    def is_admin_on_organization(self, organization_id, user):
        pass

    def can_read_organization(self, organization_id, user):
        return self._user_repository.is_user_in_organization(
            organization_id=organization_id, user=user
        )

    def can_write_organization(self, organization_id, user):
        return self._user_repository.is_admin_in_organization(
            organization_id=organization_id, user=user
        )
