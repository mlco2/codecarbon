from dependency_injector.containers import Container
from fastapi import Depends, FastAPI

from carbonserver.api.dependencies import get_query_token
from carbonserver.api.routers import (
    emissions,
    experiments,
    organizations,
    projects,
    runs,
    teams,
    users,
)
from carbonserver.database import models
from carbonserver.database.database import engine

models.Base.metadata.create_all(bind=engine)

routers = [
    emissions.router,
    runs.router,
    experiments.router,
    projects.router,
    organizations.router,
    teams.router,
    users.router
]


def create_app() -> FastAPI:
    container = Container()
    container.config.from_yaml('config.yml')
    container.wire(modules=[routers])

    db = container.db()
    db.create_database()

    app = FastAPI()
    app.container = container
    return app


app = create_app()


@app.get("/")
def default():
    return {"docs": "Please go to /docs"}


@app.get("/status")
def status():
    return {"status": "OK"}


