from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import OrganizationCreate

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


organizations_temp_db = []


@router.put("/organization", tags=["organizations"])
def add_organization(organization: OrganizationCreate, db: Session = Depends(get_db)):
    repository_organizations = SqlAlchemyRepository(db)
    org = repository_organizations.add_organization(organization)
    return {"id": org.id}


@router.get("/organization/{organization_id}", tags=["organizations"])
async def read_organization(
    organization_id: str = Path(..., title="The ID of the organization to get"),
    db: Session = Depends(get_db),
):
    repository_organizations = SqlAlchemyRepository(db)
    organization = repository_organizations.get_one_organization(organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return organization


@router.get("/organizations/{organization_id}", tags=["organizations"])
async def read_teams_organizations(
    team_id: str = Path(..., title="The ID of the team to get")
):
    # team_organizations = crud_organizations.get_Team_from_Organizations(team_id)
    # # Remove next line when DB work
    # team_organizations = organizations_temp_db
    # return team_organizations
    raise HTTPException(status_code=501, detail="Not Implemented")
