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

Measurement runs **after** the HTTP response is sent (deferred `stop_task`), so clients are not blocked on hardware sampling. By default, emissions are logged on the **`codecarbon`** logger via `log_request_complete`. Pass `on_request_complete=None` to disable logging, or supply your own callback.

A minimal runnable app lives at [`examples/fastapi_middleware.py`](https://github.com/mlco2/codecarbon/blob/master/examples/fastapi_middleware.py). Run it with:

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

`create_codecarbon_lifespan` stores the tracker on `app.state.codecarbon_tracker` for the middleware to reuse, and shuts down the middleware’s tracker background thread on exit. Without lifespan, call `shutdown_codecarbon_middleware(app)` before the process exits.

## Cloud API

Use **global config only** (`~/.codecarbon.config`). Do not add a repo-local `./.codecarbon.config`, or it will override these values when you run from the project directory.

```ini
[codecarbon]
api_endpoint = https://api.codecarbon.io
project_id = 833d292f-4460-43bd-a2f5-497bcff6dc95
experiment_id = aa69b440-014a-4562-ac06-ba7eecb023f9
```

Run `codecarbon login` to store your `api_key` in the same file.

To upload emissions to the dashboard, enable `save_to_api` (IDs are read from global config unless overridden in code):

```python
add_codecarbon_middleware(
    app,
    tracker_kwargs={"save_to_api": True},
)
```

One **run** is created per app process when the shared tracker starts; each measured request uploads one emission after the response. See [Use the Cloud API & Dashboard](cloud-api.md).

Verify logging, CSV, and API locally:

```console
CODECARBON_ALLOW_MULTIPLE_RUNS=True uv run --extra fastapi \
  python scripts/verify_fastapi_middleware_outputs.py --save-to-api
```

## Performance

Per-request tracking uses one shared `EmissionsTracker` with `start_task` / `stop_task` on a single background thread. Request-path work is scheduled ahead of deferred `stop_task` so new requests are not queued behind post-response measurement.

| Option | Effect |
|--------|--------|
| Default (deferred + `log_request_complete`) | Shared tracker; log after each request |
| `on_request_complete=None` | Same timing, no post-request logging |
| `create_codecarbon_lifespan` | Starts hardware monitoring once at boot (recommended) |

### Benchmarks (HF embedder workload)

Live `EmissionsTracker`, uvicorn HTTP, [`paraphrase-MiniLM-L3-v2`](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2), 50 timed requests, concurrency 4, `save_to_api=False`. With **`create_codecarbon_lifespan`**, the middleware uses a lightweight per-request snapshot (`mark_http_request_start` / `finish_http_request`) instead of stopping and restarting the tracker scheduler on every request. Measurement still runs **after** the response.

| Configuration | Mean (ms) | vs baseline |
|---|---:|---:|
| No middleware (baseline) | ~26 | — |
| Deferred, no logging | ~30 | ~+6–17% |
| Deferred + logging (default) | ~27 | ~+6% |

Absolute overhead is about **+1–4 ms** per request on a fast embedder baseline when the lifespan tracker is used. Older tables near **~15%** used `start_task` / `stop_task` per request (scheduler stop/start on every call). A global lock that held the whole request until `stop_task` finished inflated overhead to **~40%** — that lock is removed.

With **`save_to_api=True`**, each request also waits on a real HTTPS `add_emission`; mean latency becomes seconds under concurrency (network + serialization), not milliseconds.

Run-to-run variance is high on a single machine; treat as indicative, not a SLA. Reproduce:

```console
# Live EmissionsTracker + real HF embedder + uvicorn HTTP (recommended):
uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \
  python scripts/benchmark_fastapi_middleware.py --realistic

# Same, explicit flags:
uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \
  python scripts/benchmark_fastapi_middleware.py --workload hf-embedder --network --real-tracker

# Mocked tracker for fast CI (~10s; high % overhead with concurrency 8 + noop workload):
uv run --extra fastapi --with uvicorn python scripts/benchmark_fastapi_middleware.py --quick

# Include save_to_api (mocked upload latency, api_call_interval=1):
uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \
  python scripts/benchmark_fastapi_middleware.py --workload hf-embedder --with-save-to-api
```

The script preloads the ML model once when using `hf-embedder` or `hf-classifier`, so each scenario reuses the same weights instead of reloading.

With ``save_to_api=True`` and ``create_codecarbon_lifespan``, each finalized
request uploads one emission via ``persist_completed_task`` (after ``stop_task``).
Sub-second requests are sent with API duration rounded up to 1 second. A final
``tracker.stop()`` still flushes run-level totals and any tasks not yet uploaded.

Requires a valid ``api_key`` and ``experiment_id`` in ``~/.codecarbon.config``
(``codecarbon login``). The repo ``.codecarbon.config`` must not override those
with empty values.

Custom logging callback (replaces the default):

```python
from codecarbon.integrations.fastapi import add_codecarbon_middleware

add_codecarbon_middleware(
    app,
    on_request_complete=lambda request, response, data, task_name: logger.info(
        "%s emissions=%s", task_name, getattr(data, "emissions", None)
    ),
)
```

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

## `task_name_formatter`, `on_request_complete`

- **`task_name_formatter`** — optional `(Request) -> str` override; default is `METHOD /route/template`.
- **`on_request_complete`** — optional `(request, response, emissions_data | None, task_name) -> None`; default logs via `log_request_complete`; `None` disables the callback.

## Middleware order

Per [FastAPI middleware order](https://fastapi.tiangolo.com/tutorial/middleware/), the **last** middleware added is **outermost** on the request path (runs first on the way in). Add CodeCarbon **after** other middleware so it wraps inner layers and includes work done by inner middleware and route handlers:

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware, ...)
add_codecarbon_middleware(app)  # outermost on request → measures the full stack below
```

## Limitations (v1)

- **WebSockets** are not instrumented by this middleware.
- **Background tasks** (`BackgroundTasks` and similar) run **after** the middleware has finished the request path; their CPU/GPU use may **not** be fully attributed to that request’s measurement window.
- **Response headers** for emissions are not supported by this middleware (measurement is deferred after the response). Use logging, a custom `on_request_complete` handler, or the [`@track_emissions` decorator](../reference/api.md#track_emissions-decorator) for per-route control.

## Per-endpoint tracking

For a single route or fine-grained control without global middleware, use the [`@track_emissions` decorator](../reference/api.md#track_emissions-decorator) (same parameters as `EmissionsTracker`).
