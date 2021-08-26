from container import ServerContainer
from fastapi import Depends, FastAPI
from fastapi_pagination import add_pagination
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from carbonserver.api.dependencies import get_query_token
from carbonserver.api.errors import DBException
from carbonserver.api.infra.database import sql_models
from carbonserver.api.routers import (
    authenticate,
    emissions,
    experiments,
    organizations,
    projects,
    runs,
    teams,
    users,
)
from carbonserver.database.database import engine


async def db_exception_handler(request: Request, exc: DBException):
    return JSONResponse({"detail": exc.error.message}, status_code=400)


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse({"detail": "Generic error"}, status_code=500)


async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        {
            "detail": "Validation error : a data is missing or in wrong format. Could be an error in our answer, not only in your request"
        },
        status_code=400,
    )


def create_app() -> FastAPI:

    container = init_container()

    init_db(container)
    server = init_server(container)
    server.add_exception_handler(DBException, db_exception_handler)
    server.add_exception_handler(ValidationError, validation_exception_handler)
    server.add_exception_handler(Exception, generic_exception_handler)

    return server


def init_container():
    container = ServerContainer()
    container.wire(
        modules=[
            emissions,
            runs,
            experiments,
            projects,
            teams,
            organizations,
            users,
            authenticate,
        ]
    )
    return container


def init_db(container):
    db = container.db()
    db.create_database()
    sql_models.Base.metadata.create_all(bind=engine)


def init_server(container):
    server = FastAPI(dependencies=[Depends(get_query_token)])
    server.container = container
    server.include_router(users.router)
    server.include_router(authenticate.router)
    server.include_router(organizations.router)
    server.include_router(teams.router)
    server.include_router(projects.router)
    server.include_router(experiments.router)
    server.include_router(experiments.router)
    server.include_router(runs.router)
    server.include_router(emissions.router)

    return server


app = create_app()
add_pagination(app)


@app.get("/")
def default():
    return {"status": "OK"}
