"""Minimal FastAPI app with CodeCarbon middleware."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    create_codecarbon_lifespan,
)

_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
_OUTPUT_DIR.mkdir(exist_ok=True)

# api_key, experiment_id, project_id: read from ~/.codecarbon.config (not repo .codecarbon.config).
_tracker_kwargs = {
    "save_to_file": True,
    "save_to_api": True,
    "save_to_logger": False,
    "log_level": "info",
    "output_dir": str(_OUTPUT_DIR),
    "allow_multiple_runs": True,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_codecarbon_lifespan(
        app,
        project_name="fastapi-demo",
        **_tracker_kwargs,
    ):
        yield


def report(request, response, emissions_data, task_name):
    """Report per request, honestly: never a zero standing in for unknown."""
    measurement = request.state.codecarbon
    if emissions_data is not None:
        print(
            f"{task_name}: tier={measurement.tier.value} "
            f"emissions={emissions_data.emissions} kg "
            f"energy={emissions_data.energy_consumed} kWh"
        )
    else:
        print(
            f"{task_name}: tier={measurement.tier.value} "
            f"emissions=unavailable ({measurement.unavailable_reason})"
        )


app = FastAPI(title="CodeCarbon FastAPI demo", lifespan=lifespan)
add_codecarbon_middleware(
    app,
    project_name="fastapi-demo",
    tracker_kwargs=_tracker_kwargs,
    on_request_complete=report,
    response_headers=True,  # opt-in; adds X-CodeCarbon-Tier
)


@app.get("/predict")
def predict(text: str = "hello"):
    return {"text": text, "label": "demo"}


@app.get("/totals")
def totals():
    """Per-endpoint aggregates: the only energy output in the aggregate_only tier."""
    middleware = app.state.codecarbon_middleware
    return {
        "tier": middleware.measurement_tier,
        "endpoints": {
            key: vars(value) for key, value in middleware.endpoint_totals().items()
        },
    }


# Per-request: codecarbon logger (INFO) after each response.
# CSV: examples/output/emissions.csv on shutdown.
# Run:
#   CODECARBON_ALLOW_MULTIPLE_RUNS=True uv run --extra fastapi --with uvicorn \
#     uvicorn examples.fastapi_middleware:app --reload
#   curl 'http://127.0.0.1:8000/predict?text=hello'
