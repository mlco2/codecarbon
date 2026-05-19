# FastAPI middleware

Track HTTP request carbon emissions for a [FastAPI](https://fastapi.tiangolo.com/) (or Starlette) app with optional response headers. Install the optional integration extra, register the middleware, and each route is measured without per-handler boilerplate.

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
add_codecarbon_middleware(app, project_name="my-api", response_headers="default")
```

A minimal runnable app lives at [`examples/fastapi_middleware.py`](https://github.com/mlco2/codecarbon/blob/master/examples/fastapi_middleware.py). Run it with:

```console
uv run --extra fastapi uvicorn examples.fastapi_middleware:app --reload
```

Then open or `curl` `http://127.0.0.1:8000/predict` and inspect response headers for CodeCarbon fields.

## `tracking_mode`: `request` vs `app`

| Mode | Behavior |
|------|-----------|
| **`request`** (default) | Creates a short-lived `EmissionsTracker` per HTTP request. Safe under concurrency; each request is isolated. |
| **`app`** | Reuses one tracker on `app.state` and uses `start_task` / `stop_task` per request (with an asyncio lock). Lower overhead; measurements for concurrent requests are serialized. |

Use **`request`** unless you have measured a need for a shared tracker.

## Lifespan pattern for `tracking_mode="app"`

When using **`app`** mode, start and stop the shared tracker with the application lifespan so totals flush on shutdown:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from codecarbon.integrations.fastapi import add_codecarbon_middleware, create_codecarbon_lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_codecarbon_lifespan(app, project_name="my-api"):
        yield


app = FastAPI(lifespan=lifespan)
add_codecarbon_middleware(app, tracking_mode="app", response_headers="default")
```

`create_codecarbon_lifespan` stores the tracker on `app.state.codecarbon_tracker` for the middleware to reuse.

## Response headers

### Presets

| Preset | Typical use |
|--------|----------------|
| **`emissions`** | Single header for CO₂ (kg). |
| **`default`** | Emissions, energy consumed, duration, emissions rate. |
| **`energy`** | Emissions plus per-subsystem energy (`cpu_energy`, `gpu_energy`, `ram_energy`) and duration. |
| **`power`** | Emissions plus instantaneous power components and duration. |
| **`full`** | All supported numeric fields, each with an auto-generated `X-CodeCarbon-…` header name. |

`True` is an alias for the **`emissions`** preset; `False` or `None` disables optional headers.

### Field lists and custom maps

Pass a **list of field names** to emit those metrics with auto-named headers (derived from the field and unit).

Pass a **dict** mapping `EmissionsData` field names to exact header names for full control:

```python
add_codecarbon_middleware(
    app,
    response_headers={
        "emissions": "X-MyApp-Carbon-kg",
        "energy_consumed": "X-MyApp-Energy-kwh",
        "duration": "X-MyApp-Duration-s",
    },
)
```

### `header_formatter`

For JSON, extra headers, or non-standard formatting, pass **`header_formatter`** as a callable `(EmissionsData, Request) -> dict[str, str]`. When set, it replaces preset/list/dict mapping for response headers.

## `exclude_paths`, `task_name_formatter`, `on_request_complete`

- **`exclude_paths`**: Iterable of path prefixes to skip (no tracker work). The default set includes common docs and health paths (for example `/docs`, `/openapi.json`, `/health`). Passing your own iterable **replaces** that default; use the defaults, extend them in code, or list only what you need.
- **`task_name_formatter`**: Callable `(Request) -> str` to override how the task name is built (default is `METHOD` + matched route template or path).
- **`on_request_complete`**: Optional callback after each tracked request: `(request, response, emissions_data, task_name)` for logging, metrics backends, or custom side effects.

## CORS and `expose_headers`

If the browser must read CodeCarbon headers (e.g. in JavaScript `fetch`), configure **`expose_headers`** on `CORSMiddleware` to list the header names you emit (browsers do not expose arbitrary response headers to frontend code by default).

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

## Per-endpoint tracking

For a single route or fine-grained control without global middleware, use the [`@track_emissions` decorator](../reference/api.md#track_emissions-decorator) (same parameters as `EmissionsTracker`).
