import os

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from carbonserver.api.errors import DBException, UserException, get_http_exception
from carbonserver.api.infra.database import sql_models, telemetry_sql_models
from carbonserver.api.routers import (
    authenticate,
    emissions,
    experiments,
    organizations,
    project_api_tokens,
    projects,
    runs,
    telemetry,
)
from carbonserver.api.services import auth_service
from carbonserver.config import DEV_ENVIRONMENTS, settings
from carbonserver.container import ServerContainer
from carbonserver.database.database import engine
from carbonserver.logger import logger


async def db_exception_handler(request: Request, exc: DBException):
    return JSONResponse({"detail": exc.error.message}, status_code=400)


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse({"detail": "Generic error"}, status_code=500)


async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"ValidationError {exc}")
    return JSONResponse(
        {
            "detail": "Validation error : a data is missing or in wrong format. Could be an error in our answer, not only in your request",
            "validation_error_message": str(exc),
        },
        status_code=400,
    )


async def user_exception_handler(request: Request, exc: UserException):
    http_exc = get_http_exception(exc)
    return JSONResponse({"detail": http_exc.detail}, status_code=http_exc.status_code)


def create_app() -> FastAPI:
    container = init_container()

    init_db(container)
    server = init_server(container)
    server.add_exception_handler(DBException, db_exception_handler)
    server.add_exception_handler(UserException, user_exception_handler)
    server.add_exception_handler(ValidationError, validation_exception_handler)
    server.add_exception_handler(Exception, generic_exception_handler)
    server.add_middleware(SessionMiddleware, secret_key=get_session_secret_key())

    return server


def get_session_secret_key() -> str:
    """
    Key signing the session cookie that holds the OAuth login state.
    Set SESSION_SECRET_KEY outside development: the random fallback differs in
    every worker and after every restart, which breaks logins in progress.
    """
    if settings.session_secret_key:
        return settings.session_secret_key
    if settings.environment in DEV_ENVIRONMENTS:
        return "dev-secret-key"
    logger.warning(
        "SESSION_SECRET_KEY is not set: using a random key, so sessions do not "
        "survive a restart and are not shared between workers."
    )
    return os.urandom(32).hex()


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
            telemetry,
            authenticate,
            auth_service,
        ]
    )
    return container


def init_db(container):
    db = container.db()
    db.create_database()
    sql_models.Base.metadata.create_all(bind=engine)
    telemetry_sql_models.Base.metadata.create_all(bind=engine)


def init_server(container):
    server = FastAPI(
        servers=[
            {"url": "/api/"},
        ],
    )

    server.container = container
    server.include_router(authenticate.router)
    server.include_router(organizations.router)
    server.include_router(projects.router)
    server.include_router(project_api_tokens.router)
    server.include_router(experiments.router)
    server.include_router(runs.router)
    server.include_router(emissions.router)
    server.include_router(telemetry.router)
    add_pagination(server)

    server.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return server


def get_cors_origins() -> list[str]:
    """
    Origins allowed to call the API with credentials: the public dashboards,
    localhost in development only, CORS_ORIGINS (comma separated) and FRONTEND_URL.
    """
    origins = [
        "https://api.codecarbon.io",
        "https://dashboard.codecarbon.io",
        "https://dash-dev.cleverapps.io/",
        "https://dash-dev.cleverapps.io/api",
    ]
    if settings.environment in DEV_ENVIRONMENTS:
        origins += [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    raw_cors = os.environ.get("CORS_ORIGINS", "")
    origins += [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
    if settings.frontend_url != "":
        origins.append(settings.frontend_url)
    return origins


app = create_app()
app.mount("/api", app, name="api")


@app.get("/")
def default():
    return {"status": "OK"}
