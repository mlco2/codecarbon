from carbonserver.database import models, schemas

import abc


class Organizations(abc.ABC):
    @abc.abstractmethod
    def add_organization(self, organization: schemas.OrganizationCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_db_to_class(
        self, organization: models.Organization
    ) -> schemas.Organization:
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_organization(self, organization_id):
        raise NotImplementedError

    @abc.abstractmethod
    def get_team_from_organizations(self, organization_id):
        raise NotImplementedError
