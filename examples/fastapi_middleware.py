"""Minimal FastAPI app with CodeCarbon middleware."""

from fastapi import FastAPI

from codecarbon.integrations.fastapi import add_codecarbon_middleware

app = FastAPI(title="CodeCarbon FastAPI demo")
add_codecarbon_middleware(
    app,
    project_name="fastapi-demo",
    response_headers="default",
)

# Or expose a custom subset:
# response_headers=["emissions", "energy_consumed", "duration", "cpu_power", "gpu_power"]


@app.get("/predict")
def predict(text: str = "hello"):
    return {"text": text, "label": "demo"}


# Run: uv run --extra fastapi uvicorn examples.fastapi_middleware:app --reload
