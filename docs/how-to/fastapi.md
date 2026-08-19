# FastAPI middleware

Track HTTP request carbon emissions for a [FastAPI](https://fastapi.tiangolo.com/) (or Starlette) app. Install the optional integration extra, register the middleware, and each route is measured without per-handler boilerplate.

## Install

```console
pip install "codecarbon[fastapi]"
```

With uv:

```console
uv add "codecarbon[fastapi]"
```

## Basic usage

```python
from fastapi import FastAPI
from codecarbon.integrations.fastapi import add_codecarbon_middleware

app = FastAPI()
add_codecarbon_middleware(app, project_name="my-api")
```

By default, measurement runs after the response is sent (clients are not blocked on hardware sampling), and emissions are logged on the `codecarbon` logger. Pass `on_request_complete=None` to turn logging off, or supply your own callback.

A minimal runnable app lives at [`examples/fastapi_middleware.py`](https://github.com/mlco2/codecarbon/blob/master/examples/fastapi_middleware.py). For a production-style setup with a Hugging Face embedder and safe concurrent requests, see [`examples/fastapi_embedder.py`](https://github.com/mlco2/codecarbon/blob/master/examples/fastapi_embedder.py). Run it with:

```console
uv run --extra fastapi uvicorn examples.fastapi_middleware:app --reload
```

Then open or `curl` `http://127.0.0.1:8000/predict` and check application logs for per-request emissions.

## Lifespan (recommended)

Start one shared `EmissionsTracker` at boot and flush on shutdown:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from codecarbon.integrations.fastapi import add_codecarbon_middleware, create_codecarbon_lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_codecarbon_lifespan(app, project_name="my-api"):
        yield


app = FastAPI(lifespan=lifespan)
add_codecarbon_middleware(app)
```

`create_codecarbon_lifespan` puts a shared tracker on `app.state` for the middleware to reuse and stops it cleanly on shutdown. If you skip lifespan, call `shutdown_codecarbon_middleware(app)` before exit.

## Measurement model

- **Default (deferred):** response is sent first; finalize runs on a dedicated tracker worker thread; sampling is synchronous on that worker before `on_request_complete`.
- **`response_headers=...`:** measure before `http.response.start` and inject `X-CodeCarbon-*` headers (adds sampling latency on the client path). Header values cover work up to response start, not post-body background tasks.
- With `create_codecarbon_lifespan`, concurrent requests on the same route get unique internal task IDs via `HttpRequestBaseline`.

## Cloud API

Use **global config only** (`~/.codecarbon.config`). Do not add a repo-local `./.codecarbon.config`, or it will override these values when you run from the project directory.

```ini
[codecarbon]
api_endpoint = https://api.codecarbon.io
project_id = 00000000-0000-0000-0000-000000000001
experiment_id = 00000000-0000-0000-0000-000000000002
```

Run `codecarbon login` to store your `api_key` in the same file (never commit it).

To upload emissions to the dashboard, enable `save_to_api` (IDs are read from global config unless overridden in code):

```python
add_codecarbon_middleware(
    app,
    tracker_kwargs={"save_to_api": True},
)
```

One **run** is created per app process when the shared tracker starts; each measured request uploads one emission after the response. See [Use the Cloud API & Dashboard](cloud-api.md).

## Performance overview

By default, CodeCarbon measures **after** the response is sent. Clients see only a small amount of middleware bookkeeping; hardware sampling and logging run on a background tracker worker.

| Mode | Client path | When to use |
|------|-------------|-------------|
| Deferred + logging (default) | Response first, then measure | Most APIs |
| Deferred, `on_request_complete=None` | Response first, measure without log | Lowest overhead while still tracking |
| `response_headers=True` | Measure **before** `http.response.start` | Clients need `X-CodeCarbon-*` headers |
| `create_codecarbon_lifespan` | Same as above + one shared tracker | Production (recommended) |

### Measured overhead (HF embedder, live tracker)

Benchmarked with a **live** `EmissionsTracker`, [`paraphrase-MiniLM-L3-v2`](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2), uvicorn and `create_codecarbon_lifespan`, over 50 timed requests after 5 warmup requests, at concurrency 4.

Measured on **Darwin arm64**, Python 3.12 (**2026-07-29**):

| Setup | Mean response time | vs baseline |
|--------|-------------------:|------------:|
| No middleware | 42 ms | — |
| Deferred, logging off | 30 ms | ~same order as baseline |
| Deferred + logging (default) | 32 ms | ~same order as baseline |
| Sync headers (`response_headers=True`) | 52 ms | **~+24%** |

**What this means**

- **Deferred (default):** response is sent before finalize; client latency stays in the same ballpark as inference under concurrency (not hundreds of ms).
- **Request path:** mark runs on the tracker REQUEST lane; finalize reuses cached metadata and skips redundant power samples when the scheduler is fresh.
- **Sync headers:** measure before `http.response.start`; latency includes sample time on the client path when a fresh hardware read is needed.
- **`save_to_api=True`:** uploads after the response; network time is not on the HTTP critical path in deferred mode.

Prefer deferred + logging/API unless clients need response headers.

## `include` and `exclude`

Two filters control which requests are measured. Both accept the same pattern forms:

| Pattern | Meaning |
|---------|---------|
| `GET /predict` | One HTTP method on one route |
| `/predict` | Any method on that route (`include`), or skip that route/URL prefix (`exclude`) |

- **`exclude`** — skip matching requests. Defaults to docs and health paths (`/docs`, `/health`, …). Pass your own list to replace the default.
- **`include`** — when set, only matching endpoints are tracked (allowlist).

```python
add_codecarbon_middleware(
    app,
    include=["GET /predict", "POST /train"],
    exclude=["GET /admin", "/internal"],
)
```

## `response_headers`, `include_background_tasks`, `task_name_formatter`, `on_request_complete`

- **`response_headers`** — `True` (emissions only) or a list of field names (`emissions`, `duration`, `energy_consumed`, …). Measures before the response starts and sets `X-CodeCarbon-*` headers. Default `None` / off (deferred, no headers).
- **`include_background_tasks`** — default `True`: FastAPI/Starlette `BackgroundTasks` on the response are included. Set `False` to finalize at end of body and exclude post-body background work.
- **`task_name_formatter`** — optional `(Request) -> str`; default is `METHOD /route/template`. Concurrent requests on the same route still get unique internal task IDs with `create_codecarbon_lifespan`.
- **`on_request_complete`** — optional callback `(request, status_code, emissions_data, task_name)`; default logs via `log_request_complete`; `None` disables it.

```python
add_codecarbon_middleware(
    app,
    response_headers=["emissions", "energy_consumed", "duration"],
    include_background_tasks=False,
)
```

## Middleware order

Per [FastAPI middleware order](https://fastapi.tiangolo.com/tutorial/middleware/), the **last** middleware added is **outermost** on the request path (runs first on the way in). Add CodeCarbon **after** other middleware so it wraps inner layers and includes work done by inner middleware and route handlers:

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware, ...)
add_codecarbon_middleware(app)  # outermost on request → measures the full stack below
```

## Limitations (v1)

- **WebSockets** are not supported. The middleware ignores non-`http` scopes and does not wrap connect/disconnect or messages.
- **Background tasks:** by default, FastAPI/Starlette `BackgroundTasks` / `Response.background` **are included** (they finish before deferred finalize). Use `include_background_tasks=False` to measure only through the response body. Fire-and-forget `asyncio.create_task`, unjoined threads, and external queues (Celery, RQ, …) are **not** tracked.
- **Response headers** require `response_headers=...` (sync measure). Deferred mode cannot attach real emissions to headers because values are computed after the response is sent.

## Per-endpoint tracking

For a single route or fine-grained control without global middleware, use the [`@track_emissions` decorator](../reference/api.md#track_emissions-decorator) (same parameters as `EmissionsTracker`).
