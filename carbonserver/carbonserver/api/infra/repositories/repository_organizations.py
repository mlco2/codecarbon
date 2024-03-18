from contextlib import AbstractContextManager
from typing import List
from uuid import UUID, uuid4

from dependency_injector.providers import Callable
from fastapi import HTTPException
from sqlalchemy import and_, func

from carbonserver.api.domain.organizations import Organizations
from carbonserver.api.infra.api_key_service import generate_api_key
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.infra.database.sql_models import (
    Organization as SqlModelOrganization,
)
from carbonserver.api.infra.database.sql_models import Project as SqlModelProject
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.infra.database.sql_models import Team as SqlModelTeam
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationReport,
)

"""
Here there is all the method to manipulate the organization data
"""


class SqlAlchemyRepository(Organizations):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_organization(self, organization: OrganizationCreate) -> Organization:
        with self.session_factory() as session:
            db_organization = SqlModelOrganization(
                id=uuid4(),
                name=organization.name,
                description=organization.description,
                api_key=generate_api_key(),
            )
            existing_organization = ( 
                                       session.query(SqlModelOrganization).filter(SqlModelOrganization.name == organization.name).first()
                                    )
            if existing_organization: 
                raise HTTPException( 
                                      status_code=404,detail=f"the organization name  {organization.name} is already existed"
                                   )
            
            session.add(db_organization)
            session.commit()
            session.refresh(db_organization)
            return self.map_sql_to_schema(db_organization)

    def get_one_organization(self, organization_id: str) -> Organization:
        """Find the organization in database and return it

        :organization_id: The id of the organization to retreive.
        :returns: An Organization in pyDantic BaseModel format.
        :rtype: schemas.Organization
        """
        with self.session_factory() as session:
            e = (
                session.query(SqlModelOrganization)
                .filter(SqlModelOrganization.id == organization_id)
                .first()
            )
            if e is None:
                raise HTTPException(
                    status_code=404, detail=f"Organization {organization_id} not found"
                )
            return self.map_sql_to_schema(e)

    def list_organizations(self) -> List[Organization]:
        with self.session_factory() as session:
            e = session.query(SqlModelOrganization)
            if e is None:
                return []
            orgs: List[Organization] = []
            for org in e:
                orgs.append(self.map_sql_to_schema(org))
            return orgs

    def is_api_key_valid(self, organization_id: UUID, api_key: str):
        with self.session_factory() as session:
            return bool(
                session.query(SqlModelOrganization)
                .filter(SqlModelOrganization.id == organization_id)
                .filter(SqlModelOrganization.api_key == api_key)
                .first()
            )

    def get_organization_detailed_sums(
        self, organization_id, start_date, end_date
    ) -> OrganizationReport:
        """Find the emissions of an organization in database between two dates and return
        a report containing their sum

        :organization_id: The id of the organization to retrieve emissions from
        :start_date: the lower bound of the time interval which contains sought emissions
        :end_date: the upper bound of the time interval which contains sought emissions
        :returns: A report containing the sums of emissions
        :rtype: schemas.ProjectReport
        """
        with self.session_factory() as session:
            res = (
                session.query(
                    SqlModelOrganization.id.label("organization_id"),
                    SqlModelOrganization.name,
                    SqlModelOrganization.description,
                    func.sum(SqlModelEmission.emissions_sum).label("emissions"),
                    func.avg(SqlModelEmission.cpu_power).label("cpu_power"),
                    func.avg(SqlModelEmission.gpu_power).label("gpu_power"),
                    func.avg(SqlModelEmission.ram_power).label("ram_power"),
                    func.sum(SqlModelEmission.cpu_energy).label("cpu_energy"),
                    func.sum(SqlModelEmission.gpu_energy).label("gpu_energy"),
                    func.sum(SqlModelEmission.ram_energy).label("ram_energy"),
                    func.sum(SqlModelEmission.energy_consumed).label("energy_consumed"),
                    func.sum(SqlModelEmission.duration).label("duration"),
                    func.avg(SqlModelEmission.emissions_rate).label("emissions_rate"),
                    func.count(SqlModelEmission.emissions_rate).label(
                        "emissions_count"
                    ),
                )
                .join(
                    SqlModelTeam,
                    SqlModelOrganization.id == SqlModelTeam.organization_id,
                    isouter=True,
                )
                .join(
                    SqlModelProject,
                    SqlModelTeam.id == SqlModelProject.team_id,
                    isouter=True,
                )
                .join(
                    SqlModelExperiment,
                    SqlModelProject.id == SqlModelExperiment.project_id,
                    isouter=True,
                )
                .join(
                    SqlModelRun,
                    SqlModelExperiment.id == SqlModelRun.experiment_id,
                    isouter=True,
                )
                .join(
                    SqlModelEmission,
                    SqlModelRun.id == SqlModelEmission.run_id,
                    isouter=True,
                )
                .filter(SqlModelOrganization.id == organization_id)
                .filter(
                    and_(SqlModelEmission.timestamp >= start_date),
                    (SqlModelEmission.timestamp <= end_date),
                )
                .group_by(
                    SqlModelOrganization.id,
                    SqlModelOrganization.name,
                    SqlModelOrganization.description,
                )
                .first()
            )
            return res

    @staticmethod
    def map_sql_to_schema(organization: SqlModelOrganization) -> Organization:
        return Organization(
            id=str(organization.id),
            name=organization.name,
            description=organization.description,
            api_key=organization.api_key,
        )
