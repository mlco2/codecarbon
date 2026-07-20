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

Measurement runs after the response is sent, so clients are not blocked on hardware sampling. By default, emissions are logged on the `codecarbon` logger. Pass `on_request_complete=None` to turn logging off, or supply your own callback.

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

`create_codecarbon_lifespan` puts a shared tracker on `app.state` for the middleware to reuse and stops it cleanly on shutdown. If you skip lifespan, call `shutdown_codecarbon_middleware(app)` before exit.

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

Emissions are measured **after** the response is sent, so your API clients are not waiting on hardware sampling. One shared tracker runs in the background.

| Setup | What it does |
|--------|--------|
| Default | Log emissions after each request |
| `on_request_complete=None` | Track emissions without logging |
| `create_codecarbon_lifespan` | Start the tracker once at boot (recommended) |

### How much does it cost?

We benchmarked a small sentence embedder ([`paraphrase-MiniLM-L3-v2`](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2)) serving 50 requests at concurrency 4 over uvicorn:

| Setup | Avg. response time |
|--------|-------------------:|
| No middleware | 24 ms |
| With middleware, logging off | 24 ms |
| With middleware (default) | 27 ms |

On that workload, default middleware adds about **~3 ms** per request. Your numbers will vary with model size, hardware, and concurrency.

With `save_to_api=True`, each request also uploads to the CodeCarbon API after the response, which adds network time on top of the above.

To run the same benchmark locally:

```console
uv run --extra fastapi --with uvicorn --with sentence-transformers --with torch \
  python scripts/benchmark_fastapi_middleware.py \
  --workload hf-embedder --network --requests 50 --warmup 5 --concurrency 4
```

For a quick smoke test (no ML model):

```console
uv run --extra fastapi python scripts/benchmark_fastapi_middleware.py --quick
```

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
