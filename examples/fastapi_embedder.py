"""FastAPI embedder API with CodeCarbon middleware (production-style setup).

Uses ``create_codecarbon_lifespan`` so one shared tracker handles concurrent
requests safely via ``mark_http_request_start`` / ``finish_http_request``.

Run::

    uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \\
        uvicorn examples.fastapi_embedder:app --host 127.0.0.1 --port 8000

Load test (optional)::

    uv run --extra fastapi --with httpx python -c "
    import asyncio, httpx
    async def main():
        sem = asyncio.Semaphore(4)
        async def one():
            async with sem:
                async with httpx.AsyncClient(timeout=60) as c:
                    r = await c.get('http://127.0.0.1:8000/embed', params={'text': 'hello'})
                    r.raise_for_status()
        await asyncio.gather(*[one() for _ in range(20)])
    asyncio.run(main())
    "
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

from codecarbon.integrations.fastapi import (
    add_codecarbon_middleware,
    create_codecarbon_lifespan,
)

MODEL_ID = "sentence-transformers/paraphrase-MiniLM-L3-v2"
SAMPLE_TEXT = "CodeCarbon measures the carbon footprint of machine learning workloads."

_tracker_kwargs = {
    "save_to_file": False,
    "save_to_api": False,
    "save_to_logger": False,
    "allow_multiple_runs": True,
    "measure_power_secs": 2,
}


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_ID)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    async with create_codecarbon_lifespan(
        app,
        project_name="fastapi-embedder",
        **_tracker_kwargs,
    ):
        yield


app = FastAPI(title="CodeCarbon embedder demo", lifespan=lifespan)
add_codecarbon_middleware(
    app,
    project_name="fastapi-embedder",
    tracker_kwargs=_tracker_kwargs,
)


@app.get("/embed")
def embed(text: str = SAMPLE_TEXT) -> dict[str, Any]:
    vector = _load_model().encode(text)
    return {"dimensions": int(vector.shape[0]), "model": MODEL_ID}
