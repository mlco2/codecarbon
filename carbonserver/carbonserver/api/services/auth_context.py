class AuthContext:

    def __init__(self, user_repository, token_repository):
        self._user_repository = user_repository
        self._token_repository = token_repository

    @staticmethod
    def isOperationAuthorizedOnOrg(organization_id, user):
        return str(organization_id) in user.organizations

    def isOperationAuthorizedOnProject(self, project_id, user):
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)
