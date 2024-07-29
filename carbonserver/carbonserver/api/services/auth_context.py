class AuthContext:

    def __init__(self, user_repository, token_repository):
        self._user_repository = user_repository
        self._token_repository = token_repository

    def isOperationAuthorizedOnOrg(self, organization_id, user):
        db_user = self._user_repository.get_user_by_id(user.id)
        return organization_id in db_user.organizations

    def isOperationAuthorizedOnProject(self, project_id, user):
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)

    def isTokenAuthorizedOnExpriment(self, experiment_id, token):
        return self._token_repository.get_project_token_by_experiment_id_and_token(experiment_id, token)

    def isTokenAuthorizedOnProject(self, experiment_id, token):
        return self._token_repository.get_project_token_by_experiment_id_and_token(experiment_id, token)
