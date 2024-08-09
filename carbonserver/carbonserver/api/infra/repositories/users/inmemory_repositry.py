from typing import List

from carbonserver.carbonserver.api.domain.users import Users


class InMemoryRepository(Users):
    def __init__(self):
        self.users: List[Users] = []

    def get_user_by_id(self, user_id: str):
        return list(filter(lambda x: x.id == user_id, self.users))[0]
