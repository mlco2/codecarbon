from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Team, TeamCreate
from carbonserver.api.services.team_service import TeamService

TEAMS_ROUTER_TAGS = ["Teams"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/team",
    tags=TEAMS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
)
@inject
def add_team(
    team: TeamCreate,
    team_service: TeamService = Depends(Provide[ServerContainer.team_service]),
):
    return team_service.add_team(team)


@router.get(
    "/team/{team_id}",
    tags=TEAMS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_team(
    team_id: str,
    team_service: TeamService = Depends(Provide[ServerContainer.team_service]),
) -> Team:
    return team_service.read_team(team_id)


@router.get(
    "/teams",
    tags=TEAMS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def list_teams(
    team_service: TeamService = Depends(Provide[ServerContainer.team_service]),
) -> List[Team]:
    return team_service.list_teams()
