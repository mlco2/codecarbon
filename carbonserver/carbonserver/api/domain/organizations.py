import abc

from carbonserver.api import schemas


class Organizations(abc.ABC):
    @abc.abstractmethod
    def add_organization(self, organization: schemas.OrganizationCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_organization(self, organization_id):
        raise NotImplementedError

    @abc.abstractmethod
    def list_organizations(self):
        raise NotImplementedError
