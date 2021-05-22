from carbonserver.carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository


class UserService:

    def __init__(self, user_repository: SqlAlchemyRepository) -> None:
        self._repository: SqlAlchemyRepository = user_repository

    def create_user(self, user):
        created_user = self._repository.create_user(user)

        return created_user
