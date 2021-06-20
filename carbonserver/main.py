from container import ServerContainer
from fastapi import Depends, FastAPI

from carbonserver.api.dependencies import get_query_token
from carbonserver.api.infra.database import sql_models
from carbonserver.api.routers import (
    emissions,
    experiments,
    organizations,
    projects,
    runs,
    teams,
    users,
)
from carbonserver.database.database import engine


def create_app() -> FastAPI:

    container = init_container()

    init_db(container)
    server = init_server(container)
    return server


def init_container():
    container = ServerContainer()
    container.wire(modules=[users, organizations, teams, runs])
    return container


def init_db(container):
    db = container.db()
    db.create_database()
    sql_models.Base.metadata.create_all(bind=engine)


def init_server(container):
    server = FastAPI(dependencies=[Depends(get_query_token)])
    server.container = container
    server.include_router(emissions.router)
    server.include_router(experiments.router)
    server.include_router(runs.router)
    server.include_router(experiments.router)
    server.include_router(projects.router)
    server.include_router(teams.router)
    server.include_router(organizations.router)

    server.include_router(users.router)

    return server


app = create_app()


@app.get("/")
def default():
    return {"status": "OK"}
