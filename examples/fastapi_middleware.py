"""Minimal FastAPI app with CodeCarbon middleware."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    create_codecarbon_lifespan,
)

_tracker_kwargs = {
    "save_to_file": False,
    "save_to_api": False,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_codecarbon_lifespan(
        app,
        project_name="fastapi-demo",
        **_tracker_kwargs,
    ):
        yield


app = FastAPI(title="CodeCarbon FastAPI demo", lifespan=lifespan)
add_codecarbon_middleware(
    app,
    project_name="fastapi-demo",
    tracking_mode="app",
    response_headers="default",
    tracker_kwargs=_tracker_kwargs,
)


@app.get("/predict")
def predict(text: str = "hello"):
    return {"text": text, "label": "demo"}


# Lowest latency (no response headers): defer_measurement=True and use on_request_complete.
# Run: uv run --extra fastapi --with uvicorn uvicorn examples.fastapi_middleware:app --reload
