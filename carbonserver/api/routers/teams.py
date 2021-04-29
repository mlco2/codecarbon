from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from carbonserver.api.dependencies import get_token_header, get_db
from carbonserver.api.database import crud_teams
from carbonserver.api.database.schemas import TeamCreate


router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


teams_temp_db = []


@router.put("/team", tags=["teams"])
def add_team(team: TeamCreate, db: Session = Depends(get_db)):
    # Remove next line when DB work
    teams_temp_db.append(team.dict())
    crud_teams.save_team(db, team)


@router.get("/team/{team_id}", tags=["teams"])
async def read_team(team_id: str = Path(..., title="The ID of the team to get")):
    team = crud_teams.get_one_team(team_id)
    if team_id is False:
        raise HTTPException(status_code=404, detail="Item not found")
    return team


@router.get("/teams/{team_id}", tags=["teams"])
async def read_project_teams(
    team_id: str = Path(
        ..., title="The ID of team to get project from"
    )  # TODO : I change this from project_id because of undefined name 'team_id' but is it what we want ?
):
    project_teams = crud_teams.get_Project_from_Teams(team_id)
    # Remove next line when DB work
    project_teams = teams_temp_db
    return project_teams
