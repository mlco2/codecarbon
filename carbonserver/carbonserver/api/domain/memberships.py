import abc

from carbonserver.api import schemas


class Memberships(abc.ABC):
    @abc.abstractmethod
    def add_user_to_organization(
        self, user_id: str, organization_id: str
    ) -> schemas.Membership:
        raise NotImplementedError

    @abc.abstractmethod
    def remove_user_from_organization(
        self, user_id: str, organization_id: str
    ) -> schemas.Membership:
        raise NotImplementedError
