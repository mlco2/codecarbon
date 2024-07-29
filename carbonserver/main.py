from container import ServerContainer
from fastapi import Depends, FastAPI
from fastapi_pagination import add_pagination
from pydantic import ValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from carbonserver.api.dependencies import get_query_token
from carbonserver.api.errors import DBException, UserException
from carbonserver.api.infra.database import sql_models
from carbonserver.api.routers import (
    authenticate,
    emissions,
    experiments,
    organizations,
    project_api_tokens,
    projects,
    runs,
    users,
)
from carbonserver.database.database import engine
from carbonserver.logger import logger


async def db_exception_handler(request: Request, exc: DBException):
    return JSONResponse(
        {"detail": exc.error.message}, status_code=status.HTTP_400_BAD_REQUEST
    )


async def user_exception_handler(request: Request, exc: UserException):
    return JSONResponse({"detail": exc.error}, status_code=status.HTTP_401_UNAUTHORIZED)


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        {"detail": "Internal error"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"ValidationError {exc}")
    return JSONResponse(
        {
            "detail": "Validation error : a data is missing or in wrong format. Could be an error in our answer, not only in your request",
            "validation_error_message": str(exc),
        },
        status_code=status.HTTP_400_BAD_REQUEST,
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
            project_api_tokens,
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
    server.include_router(projects.router)
    server.include_router(project_api_tokens.router)
    server.include_router(experiments.router)
    server.include_router(experiments.router)
    server.include_router(runs.router)
    server.include_router(emissions.router)
    add_pagination(server)
    return server


app = create_app()
app.mount("/api", app, name="api")


@app.get("/")
def default():
    return {"status": "OK"}
