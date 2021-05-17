from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from carbonserver.api.dependencies import get_token_header, get_db
from carbonserver.api.schemas import TeamCreate
from carbonserver.api.infra.repositories.repository_teams import (
    SqlAlchemyRepository,
)

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


teams_temp_db = []


@router.put("/team", tags=["teams"])
def add_team(team: TeamCreate, db: Session = Depends(get_db)):
    repository_teams = SqlAlchemyRepository(db)
    repository_teams.add_team(team)


@router.get("/team/{team_id}", tags=["teams"])
async def read_team(
    team_id: str = Path(..., title="The ID of the team to get"),
    db: Session = Depends(get_db),
):
    repository_teams = SqlAlchemyRepository(db)
    team = repository_teams.get_one_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return team


@router.get("/teams/{team_id}", tags=["teams"])
async def read_project_teams(
    project_id: str = Path(..., title="The ID of the project to get")
):
    # project_teams = crud_teams.get_Project_from_Teams(team_id)
    # Remove next line when DB work
    # project_teams = teams_temp_db
    # return project_teams
    raise HTTPException(status_code=501, detail="Not Implemented")
