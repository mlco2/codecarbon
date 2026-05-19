# FastAPI Middleware Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Ship an optional FastAPI/Starlette middleware in the main `codecarbon` package that measures CO₂ emissions per HTTP request, keyed by route (method + path template), without requiring users to wrap each endpoint manually.

**Architecture:** Add `codecarbon[fastapi]` optional extra with a `CodeCarbonMiddleware` (Starlette `BaseHTTPMiddleware`) and a small `add_codecarbon_middleware()` helper. Default mode creates one short-lived `EmissionsTracker` per request (concurrency-safe). An optional `tracking_mode="app"` reuses a single tracker with `start_task`/`stop_task` and an asyncio lock (lower overhead, serializes measurements). Route names come from `request.scope["route"].path` after routing. App shutdown flushes totals via FastAPI lifespan hook. FastAPI is **not** a core dependency.

**Tech Stack:** Python 3.10+, FastAPI/Starlette ASGI middleware, `EmissionsTracker` task API, `pytest`, `httpx`/`TestClient`, `uv`.

**References:**
- [FastAPI Middleware tutorial](https://fastapi.tiangolo.com/tutorial/middleware/)
- [FastAPI Advanced Middleware](https://fastapi.tiangolo.com/advanced/middleware/)
- Existing task API: `codecarbon/emissions_tracker.py` (`start_task`, `stop_task`, `TaskEmissionsTracker`)
- Optional-integration precedent: `codecarbon/output_methods/metrics/logfire.py` (lazy import + clear error)

---

## Design decisions

### Why middleware, not a decorator?

| Approach | Pros | Cons |
|----------|------|------|
| `@track_emissions` on each route | Fine-grained control | Easy to miss endpoints; doesn't cover mounted sub-apps |
| **HTTP middleware** | Covers all routes automatically; one line to wire | Less control per route; must handle concurrency |
| Router-level dependency | Idiomatic FastAPI | Still manual per router; harder to get route template |

Middleware is the right default for “track all endpoints.” Users who need per-function granularity keep using `@track_emissions` / `TaskEmissionsTracker`.

### Concurrency (important)

`EmissionsTracker.start_task()` allows **only one active task** per tracker instance (`_active_task` guard at `emissions_tracker.py:626`). Concurrent requests sharing one tracker will log warnings and skip measurements.

**v1 strategy — two modes:**

| Mode | Behaviour | When to use |
|------|-----------|-------------|
| `request` (default) | New `EmissionsTracker` per request; `start()` → handler → `stop()` | Production APIs with concurrent traffic |
| `app` | Shared tracker; `start_task`/`stop_task` guarded by `asyncio.Lock` | Dev/low-traffic; lower init overhead |

Document this clearly. A future issue can add true concurrent per-request tasks in the core tracker.

### Route naming

After `call_next`, read the matched route:

```python
route = request.scope.get("route")
if route is not None:
    task_name = f"{request.method} {route.path}"  # e.g. "GET /users/{user_id}"
else:
    task_name = f"{request.method} {request.url.path}"  # fallback: "GET /users/42"
```

Optional `task_name_formatter: Callable[[Request], str]` override for custom names (e.g. include operation_id from OpenAPI).

### Paths to skip

Default exclude prefix list (configurable):

- `/docs`, `/redoc`, `/openapi.json`
- `/health`, `/healthz`, `/ready`, `/live`

### Response headers (configurable)

Expose measured emissions data on the HTTP response via configurable headers (custom `X-` prefix per [FastAPI middleware docs](https://fastapi.tiangolo.com/tutorial/middleware/)).

**Three levels of control:**

| Level | Parameter | Example |
|-------|-----------|---------|
| Off | `response_headers=None` | No headers added |
| Preset | `response_headers="default"` | Curated multi-field set |
| Field pick | `response_headers=["emissions", "duration", "energy_consumed"]` | Auto-named headers |
| Rename map | `response_headers={"emissions": "X-MyApp-CO2-kg", "duration": "X-MyApp-Duration-s"}` | Full header name control |
| Custom | `header_formatter=my_fn` | `(EmissionsData, Request) -> dict[str, str]` |

**Presets** (defined in `codecarbon/integrations/fastapi/_headers.py`):

| Preset | Fields exposed |
|--------|----------------|
| `"emissions"` | `emissions` only → `X-CodeCarbon-Emissions-kg` |
| `"default"` | `emissions`, `energy_consumed`, `duration`, `emissions_rate` |
| `"energy"` | `emissions`, `energy_consumed`, `cpu_energy`, `gpu_energy`, `ram_energy`, `duration` |
| `"power"` | `emissions`, `cpu_power`, `gpu_power`, `ram_power`, `duration` |
| `"full"` | All numeric `EmissionsData` fields (excluding metadata like `run_id`) |

**Auto header naming** when using a field list or preset:

```
{field} → X-CodeCarbon-{FieldTitle}-{unit}
```

Examples: `emissions` → `X-CodeCarbon-Emissions-kg`, `duration` → `X-CodeCarbon-Duration-s`, `energy_consumed` → `X-CodeCarbon-Energy-Consumed-kwh`.

**Backward compatibility:** `include_emissions_header=True` remains as a deprecated alias for `response_headers="emissions"`. If both are set, `response_headers` wins.

**Data source:** After measurement, headers are built from `EmissionsData`:
- `request` mode: `tracker.final_emissions_data` after `stop()` (per-request tracker → total == delta)
- `app` mode: return value of `stop_task()` (task delta)

**CORS note:** Browser clients need matching `expose_headers` in `CORSMiddleware` for any custom headers beyond the defaults.

### Package placement

```
codecarbon/
  integrations/
    __init__.py
    fastapi/
      __init__.py          # public exports
      middleware.py        # CodeCarbonMiddleware, helpers
      _headers.py          # response header presets + apply logic
      lifespan.py          # optional lifespan factory
```

Keeps core package free of FastAPI imports. Future integrations (Flask, Django) can live alongside.

### Optional dependency

```toml
# pyproject.toml
[project.optional-dependencies]
fastapi = [
    "fastapi>=0.100",
]
```

Dev/test group addition:

```toml
[dependency-groups]
dev = [
    # ...existing...
    "fastapi>=0.100",
]
```

---

## Public API (target)

```python
from fastapi import FastAPI
from codecarbon.integrations.fastapi import add_codecarbon_middleware

app = FastAPI()
add_codecarbon_middleware(
    app,
    project_name="my-api",
    exclude_paths={"/health"},
    response_headers="default",  # emissions + energy + duration + rate
)

# Pick specific fields with auto-named headers:
add_codecarbon_middleware(
    app,
    response_headers=["emissions", "energy_consumed", "duration", "water_consumed"],
)

# Full control over header names:
add_codecarbon_middleware(
    app,
    response_headers={
        "emissions": "X-MyApp-Carbon-kg",
        "energy_consumed": "X-MyApp-Energy-kWh",
        "duration": "X-MyApp-Latency-s",
    },
)

# Fully custom formatter (e.g. add route name, JSON-encode a subset):
from codecarbon.output_methods.emissions_data import EmissionsData
from starlette.requests import Request

def my_headers(data: EmissionsData, request: Request) -> dict[str, str]:
    return {
        "X-CodeCarbon-Emissions-kg": f"{data.emissions:.6f}",
        "X-CodeCarbon-Route": build_task_name(request),
        "X-CodeCarbon-Energy-Wh": f"{1000 * data.energy_consumed:.3f}",
    }

add_codecarbon_middleware(app, header_formatter=my_headers)

# Or class-based:
from codecarbon.integrations.fastapi import CodeCarbonMiddleware
app.add_middleware(CodeCarbonMiddleware, project_name="my-api", response_headers="default")
```

Advanced — shared tracker + lifespan:

```python
from contextlib import asynccontextmanager
from codecarbon.integrations.fastapi import create_codecarbon_lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_codecarbon_lifespan(app, project_name="my-api", tracking_mode="app"):
        yield

app = FastAPI(lifespan=lifespan)
add_codecarbon_middleware(app, tracking_mode="app")  # reuses app.state.tracker
```

---

## Task breakdown

### Task 1: Optional dependency + package skeleton

**Files:**
- Create: `codecarbon/integrations/__init__.py`
- Create: `codecarbon/integrations/fastapi/__init__.py`
- Create: `codecarbon/integrations/fastapi/middleware.py` (stub)
- Modify: `pyproject.toml` (add `fastapi` optional extra + dev dep)

**Step 1: Write the failing import test**

Create `tests/integrations/test_fastapi_import.py`:

```python
def test_fastapi_integration_importable():
    from codecarbon.integrations.fastapi import CodeCarbonMiddleware, add_codecarbon_middleware

    assert CodeCarbonMiddleware is not None
    assert callable(add_codecarbon_middleware)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integrations/test_fastapi_import.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'codecarbon.integrations'`

**Step 3: Add skeleton files**

`codecarbon/integrations/fastapi/middleware.py`:

```python
"""FastAPI/Starlette middleware for per-request emissions tracking."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.applications import Starlette


class CodeCarbonMiddleware:
    """Stub — implemented in Task 2."""

    def __init__(self, app: "Starlette", **kwargs: object) -> None:
        raise NotImplementedError


def add_codecarbon_middleware(app: "Starlette", **kwargs: object) -> None:
    """Register CodeCarbonMiddleware on a FastAPI/Starlette app."""
    app.add_middleware(CodeCarbonMiddleware, **kwargs)
```

`codecarbon/integrations/fastapi/__init__.py`:

```python
from codecarbon.integrations.fastapi.middleware import (
    CodeCarbonMiddleware,
    add_codecarbon_middleware,
)

__all__ = ["CodeCarbonMiddleware", "add_codecarbon_middleware"]
```

**Step 4: Run test — still fails on NotImplementedError when instantiating; adjust test to only import**

**Step 5: Commit**

```bash
git add codecarbon/integrations pyproject.toml tests/integrations/test_fastapi_import.py
git commit -m "feat: add fastapi integration package skeleton"
```

---

### Task 2: Route name helper + exclude logic

**Files:**
- Create: `codecarbon/integrations/fastapi/_routing.py`
- Test: `tests/integrations/test_fastapi_routing.py`

**Step 1: Write failing tests**

```python
from unittest.mock import MagicMock

from codecarbon.integrations.fastapi._routing import (
    build_task_name,
    should_skip_path,
)


def test_build_task_name_uses_route_template():
    request = MagicMock()
    request.method = "GET"
    route = MagicMock()
    route.path = "/users/{user_id}"
    request.scope = {"route": route}
    assert build_task_name(request) == "GET /users/{user_id}"


def test_build_task_name_fallback_to_url_path():
    request = MagicMock()
    request.method = "POST"
    request.scope = {}
    request.url.path = "/webhook"
    assert build_task_name(request) == "POST /webhook"


def test_should_skip_path_matches_prefixes():
    assert should_skip_path("/health", {"/health", "/docs"})
    assert should_skip_path("/docs/oauth2-redirect", {"/docs"})
    assert not should_skip_path("/api/v1/runs", {"/health", "/docs"})
```

**Step 2: Run — expect FAIL**

Run: `uv run pytest tests/integrations/test_fastapi_routing.py -v`

**Step 3: Implement `_routing.py`**

```python
from typing import Callable, Iterable, Set

from starlette.requests import Request

DEFAULT_EXCLUDE_PATHS: Set[str] = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/healthz",
    "/ready",
    "/live",
}


def should_skip_path(path: str, exclude_paths: Iterable[str]) -> bool:
    """Return True if path starts with any excluded prefix."""
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in exclude_paths)


def build_task_name(
    request: Request,
    formatter: Callable[[Request], str] | None = None,
) -> str:
    """Build a stable task name from the matched route or URL path."""
    if formatter is not None:
        return formatter(request)
    route = request.scope.get("route")
    if route is not None:
        return f"{request.method} {route.path}"
    return f"{request.method} {request.url.path}"
```

**Step 4: Run tests — PASS**

**Step 5: Commit**

```bash
git add codecarbon/integrations/fastapi/_routing.py tests/integrations/test_fastapi_routing.py
git commit -m "feat: add fastapi route naming helpers"
```

---

### Task 2b: Response header helpers

**Files:**
- Create: `codecarbon/integrations/fastapi/_headers.py`
- Test: `tests/integrations/test_fastapi_headers.py`

**Step 1: Write failing tests**

```python
from unittest.mock import MagicMock

import pytest
from starlette.responses import Response

from codecarbon.integrations.fastapi._headers import (
    HEADER_PRESETS,
    apply_response_headers,
    resolve_header_mapping,
)
from codecarbon.output_methods.emissions_data import EmissionsData


@pytest.fixture
def emissions_data() -> EmissionsData:
    return EmissionsData(
        timestamp="2026-05-19T12:00:00",
        project_name="test",
        run_id="run-1",
        experiment_id="exp-1",
        duration=1.5,
        emissions=0.00042,
        emissions_rate=0.00028,
        cpu_power=12.0,
        gpu_power=0.0,
        ram_power=5.0,
        cpu_energy=0.003,
        gpu_energy=0.0,
        ram_energy=0.001,
        energy_consumed=0.004,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="",
        cloud_provider="",
        cloud_region="",
        os="Darwin",
        python_version="3.12",
        codecarbon_version="3.2.6",
        cpu_count=8,
        cpu_model="Apple M1",
        gpu_count=0,
        gpu_model="",
        longitude=2.35,
        latitude=48.85,
        ram_total_size=16.0,
        tracking_mode="machine",
    )


def test_resolve_header_mapping_preset_emissions():
    mapping = resolve_header_mapping("emissions")
    assert mapping == {"emissions": "X-CodeCarbon-Emissions-kg"}


def test_resolve_header_mapping_field_list():
    mapping = resolve_header_mapping(["emissions", "duration"])
    assert mapping["emissions"] == "X-CodeCarbon-Emissions-kg"
    assert mapping["duration"] == "X-CodeCarbon-Duration-s"


def test_resolve_header_mapping_custom_dict():
    custom = {"emissions": "X-App-CO2", "duration": "X-App-Time"}
    assert resolve_header_mapping(custom) == custom


def test_resolve_header_mapping_bool_true_aliases_emissions():
    assert resolve_header_mapping(True) == HEADER_PRESETS["emissions"]


def test_apply_response_headers_sets_values(emissions_data):
    response = Response(content=b"ok")
    apply_response_headers(
        response,
        emissions_data,
        {"emissions": "X-CodeCarbon-Emissions-kg", "duration": "X-CodeCarbon-Duration-s"},
    )
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.00042"
    assert response.headers["X-CodeCarbon-Duration-s"] == "1.5"


def test_apply_response_headers_ignores_unknown_fields(emissions_data):
    response = Response(content=b"ok")
    apply_response_headers(response, emissions_data, {"not_a_field": "X-Bad"})
    assert "X-Bad" not in response.headers


def test_apply_response_headers_noop_when_mapping_empty(emissions_data):
    response = Response(content=b"ok")
    apply_response_headers(response, emissions_data, {})
    assert len(response.headers) == 0
```

**Step 2: Run — FAIL**

Run: `uv run pytest tests/integrations/test_fastapi_headers.py -v`

**Step 3: Implement `_headers.py`**

```python
from typing import Callable, Mapping, Sequence, Union

from starlette.requests import Request
from starlette.responses import Response

from codecarbon.output_methods.emissions_data import EmissionsData

HeaderConfig = Union[
    bool,
    str,
    Sequence[str],
    Mapping[str, str],
    None,
]
HeaderFormatter = Callable[[EmissionsData, Request], Mapping[str, str]]

FIELD_UNITS: dict[str, str] = {
    "emissions": "kg",
    "emissions_rate": "kg-per-s",
    "duration": "s",
    "energy_consumed": "kwh",
    "cpu_energy": "kwh",
    "gpu_energy": "kwh",
    "ram_energy": "kwh",
    "water_consumed": "l",
    "cpu_power": "w",
    "gpu_power": "w",
    "ram_power": "w",
    "cpu_utilization_percent": "percent",
    "gpu_utilization_percent": "percent",
    "ram_utilization_percent": "percent",
    "ram_used_gb": "gb",
    "pue": "ratio",
    "wue": "l-per-kwh",
}

HEADER_PRESETS: dict[str, dict[str, str]] = {
    "emissions": {"emissions": "X-CodeCarbon-Emissions-kg"},
    "default": {
        "emissions": "X-CodeCarbon-Emissions-kg",
        "energy_consumed": "X-CodeCarbon-Energy-Consumed-kwh",
        "duration": "X-CodeCarbon-Duration-s",
        "emissions_rate": "X-CodeCarbon-Emissions-Rate-kg-per-s",
    },
    "energy": {
        "emissions": "X-CodeCarbon-Emissions-kg",
        "energy_consumed": "X-CodeCarbon-Energy-Consumed-kwh",
        "cpu_energy": "X-CodeCarbon-Cpu-Energy-kwh",
        "gpu_energy": "X-CodeCarbon-Gpu-Energy-kwh",
        "ram_energy": "X-CodeCarbon-Ram-Energy-kwh",
        "duration": "X-CodeCarbon-Duration-s",
    },
    "power": {
        "emissions": "X-CodeCarbon-Emissions-kg",
        "cpu_power": "X-CodeCarbon-Cpu-Power-w",
        "gpu_power": "X-CodeCarbon-Gpu-Power-w",
        "ram_power": "X-CodeCarbon-Ram-Power-w",
        "duration": "X-CodeCarbon-Duration-s",
    },
}

FULL_HEADER_FIELDS: tuple[str, ...] = tuple(FIELD_UNITS.keys())


def _auto_header_name(field: str) -> str:
    unit = FIELD_UNITS.get(field, "")
    title = "-".join(part.capitalize() for part in field.split("_"))
    suffix = f"-{unit}" if unit else ""
    return f"X-CodeCarbon-{title}{suffix}"


def resolve_header_mapping(config: HeaderConfig) -> dict[str, str]:
    """Normalize response_headers config to {field: header_name}."""
    if config is None or config is False:
        return {}
    if config is True:
        return dict(HEADER_PRESETS["emissions"])
    if isinstance(config, str):
        preset = HEADER_PRESETS.get(config)
        if preset is None:
            if config == "full":
                return {field: _auto_header_name(field) for field in FULL_HEADER_FIELDS}
            raise ValueError(f"Unknown response_headers preset: {config!r}")
        return dict(preset)
    if isinstance(config, Mapping):
        return dict(config)
    return {field: _auto_header_name(field) for field in config}


def apply_response_headers(
    response: Response,
    emissions_data: EmissionsData,
    header_mapping: Mapping[str, str],
) -> None:
    """Set response headers from EmissionsData fields."""
    for field, header_name in header_mapping.items():
        if not hasattr(emissions_data, field):
            continue
        value = getattr(emissions_data, field)
        response.headers[header_name] = str(value)
```

**Step 4: Run tests — PASS**

**Step 5: Commit**

```bash
git add codecarbon/integrations/fastapi/_headers.py tests/integrations/test_fastapi_headers.py
git commit -m "feat: add configurable fastapi response header helpers"
```

---

### Task 3: Core middleware — `tracking_mode="request"`

**Files:**
- Modify: `codecarbon/integrations/fastapi/middleware.py`
- Test: `tests/integrations/test_fastapi_middleware.py`

**Step 1: Write failing integration test**

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from codecarbon.integrations.fastapi import add_codecarbon_middleware


@pytest.fixture
def app():
    application = FastAPI()

    @application.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"item_id": item_id}

    @application.get("/health")
    def health():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="test-api",
        response_headers="emissions",
    )
    return application


@patch("codecarbon.integrations.fastapi.middleware.EmissionsTracker")
def test_middleware_tracks_routed_request(MockTracker, app):
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(
        emissions=0.001, duration=0.5, energy_consumed=0.002, emissions_rate=0.002
    )

    client = TestClient(app)
    response = client.get("/items/7")

    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.stop.assert_called_once()
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.001"


@patch("codecarbon.integrations.fastapi.middleware.EmissionsTracker")
def test_middleware_applies_default_response_headers(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, response_headers="default")
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(
        emissions=0.001,
        duration=1.2,
        energy_consumed=0.003,
        emissions_rate=0.0008,
    )

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.001"
    assert response.headers["X-CodeCarbon-Duration-s"] == "1.2"
    assert response.headers["X-CodeCarbon-Energy-Consumed-kwh"] == "0.003"


@patch("codecarbon.integrations.fastapi.middleware.EmissionsTracker")
def test_middleware_custom_header_formatter(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    def formatter(data, request):
        return {
            "X-CodeCarbon-Emissions-kg": f"{data.emissions:.4f}",
            "X-CodeCarbon-Route": request.url.path,
        }

    add_codecarbon_middleware(application, header_formatter=formatter)
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(emissions=0.001234)

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.0012"
    assert response.headers["X-CodeCarbon-Route"] == "/predict"


@patch("codecarbon.integrations.fastapi.middleware.EmissionsTracker")
def test_middleware_skips_excluded_paths(MockTracker, app):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    MockTracker.assert_not_called()
```

**Step 2: Run — FAIL**

**Step 3: Implement middleware (request mode)**

Key implementation in `middleware.py`:

```python
import asyncio
from typing import Callable, Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from codecarbon import EmissionsTracker
from codecarbon.integrations.fastapi._headers import (
    HeaderConfig,
    HeaderFormatter,
    apply_response_headers,
    resolve_header_mapping,
)
from codecarbon.integrations.fastapi._routing import (
    DEFAULT_EXCLUDE_PATHS,
    build_task_name,
    should_skip_path,
)
from codecarbon.output_methods.emissions_data import EmissionsData


class CodeCarbonMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        project_name: str = "codecarbon-fastapi",
        tracking_mode: str = "request",
        exclude_paths: Iterable[str] | None = None,
        response_headers: HeaderConfig = None,
        include_emissions_header: bool = False,
        header_formatter: HeaderFormatter | None = None,
        task_name_formatter: Callable[[Request], str] | None = None,
        on_request_complete: Callable | None = None,
        tracker_kwargs: dict | None = None,
        **emissions_tracker_kwargs,
    ) -> None:
        super().__init__(app)
        self.project_name = project_name
        self.tracking_mode = tracking_mode
        self.exclude_paths = set(exclude_paths or DEFAULT_EXCLUDE_PATHS)
        if response_headers is not None:
            self.header_mapping = resolve_header_mapping(response_headers)
        elif include_emissions_header:
            self.header_mapping = resolve_header_mapping(True)
        else:
            self.header_mapping = {}
        self.header_formatter = header_formatter
        self.task_name_formatter = task_name_formatter
        self.on_request_complete = on_request_complete
        merged = dict(tracker_kwargs or {})
        merged.update(emissions_tracker_kwargs)
        merged.setdefault("allow_multiple_runs", True)
        self.tracker_kwargs = merged
        self._app_tracker: EmissionsTracker | None = None
        self._measurement_lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if should_skip_path(request.url.path, self.exclude_paths):
            return await call_next(request)
        if self.tracking_mode == "app":
            return await self._dispatch_app_mode(request, call_next)
        return await self._dispatch_request_mode(request, call_next)

    def _apply_headers(
        self,
        response: Response,
        emissions_data: EmissionsData | None,
        request: Request,
    ) -> None:
        if response is None or emissions_data is None:
            return
        if self.header_formatter is not None:
            for name, value in self.header_formatter(emissions_data, request).items():
                response.headers[name] = value
            return
        apply_response_headers(response, emissions_data, self.header_mapping)

    async def _dispatch_request_mode(self, request: Request, call_next: Callable) -> Response:
        tracker = EmissionsTracker(project_name=self.project_name, **self.tracker_kwargs)
        tracker.start()
        response: Response | None = None
        emissions_data: EmissionsData | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            tracker.stop()
            emissions_data = getattr(tracker, "final_emissions_data", None)
            task_name = build_task_name(request, self.task_name_formatter)
            if self.on_request_complete and response is not None:
                self.on_request_complete(request, response, emissions_data, task_name)
            self._apply_headers(response, emissions_data, request)

    async def _dispatch_app_mode(self, request: Request, call_next: Callable) -> Response:
        tracker = self._get_app_tracker(request)
        task_name = build_task_name(request, self.task_name_formatter)
        response: Response | None = None
        emissions_data: EmissionsData | None = None
        async with self._measurement_lock:
            await asyncio.to_thread(tracker.start_task, task_name)
            try:
                response = await call_next(request)
                return response
            finally:
                emissions_data = await asyncio.to_thread(tracker.stop_task, task_name)
        if self.on_request_complete and response is not None:
            self.on_request_complete(request, response, emissions_data, task_name)
        self._apply_headers(response, emissions_data, request)
        return response

    def _get_app_tracker(self, request: Request) -> EmissionsTracker:
        app_tracker = getattr(request.app.state, "codecarbon_tracker", None)
        if app_tracker is not None:
            return app_tracker
        if self._app_tracker is None:
            self._app_tracker = EmissionsTracker(
                project_name=self.project_name, **self.tracker_kwargs
            )
            self._app_tracker.start()
        return self._app_tracker


def add_codecarbon_middleware(app, **kwargs) -> None:
    app.add_middleware(CodeCarbonMiddleware, **kwargs)
```

**Step 4: Run tests — PASS**

Run: `uv run pytest tests/integrations/test_fastapi_middleware.py -v`

**Step 5: Commit**

```bash
git add codecarbon/integrations/fastapi/middleware.py tests/integrations/test_fastapi_middleware.py
git commit -m "feat: implement CodeCarbonMiddleware request tracking mode"
```

---

### Task 4: Lifespan helper for app-mode shutdown

**Files:**
- Create: `codecarbon/integrations/fastapi/lifespan.py`
- Modify: `codecarbon/integrations/fastapi/__init__.py`
- Test: `tests/integrations/test_fastapi_lifespan.py`

**Step 1: Write failing test**

```python
from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from codecarbon.integrations.fastapi.lifespan import create_codecarbon_lifespan


@pytest.mark.asyncio
@patch("codecarbon.integrations.fastapi.lifespan.EmissionsTracker")
async def test_lifespan_stops_tracker_on_shutdown(MockTracker):
    tracker = MagicMock()
    MockTracker.return_value = tracker
    app = FastAPI()

    async with create_codecarbon_lifespan(app, project_name="api"):
        assert app.state.codecarbon_tracker is tracker
        tracker.start.assert_called_once()

    tracker.stop.assert_called_once()
```

**Step 2: Run — FAIL**

**Step 3: Implement `lifespan.py`**

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

from codecarbon import EmissionsTracker


@asynccontextmanager
async def create_codecarbon_lifespan(app, *, project_name: str = "codecarbon-fastapi", **tracker_kwargs) -> AsyncIterator[None]:
    tracker_kwargs.setdefault("allow_multiple_runs", True)
    tracker = EmissionsTracker(project_name=project_name, **tracker_kwargs)
    tracker.start()
    app.state.codecarbon_tracker = tracker
    try:
        yield
    finally:
        tracker.stop()
        app.state.codecarbon_tracker = None
```

Export from `__init__.py`.

**Step 4: Run tests — PASS**

**Step 5: Commit**

```bash
git add codecarbon/integrations/fastapi/lifespan.py codecarbon/integrations/fastapi/__init__.py tests/integrations/test_fastapi_lifespan.py
git commit -m "feat: add fastapi lifespan helper for shared tracker"
```

---

### Task 5: Graceful import when FastAPI not installed

**Files:**
- Modify: `codecarbon/integrations/fastapi/middleware.py`
- Test: `tests/integrations/test_fastapi_import.py`

**Step 1: Write test**

```python
def test_missing_fastapi_shows_helpful_error(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("starlette") or name.startswith("fastapi"):
            raise ImportError("no fastapi")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    with pytest.raises(ImportError, match="pip install codecarbon\\[fastapi\\]"):
        from codecarbon.integrations.fastapi.middleware import CodeCarbonMiddleware  # noqa: F401
```

Pattern: wrap Starlette imports in try/except at module level (same as LogfireOutput).

**Step 2–4: Implement, verify PASS**

**Step 5: Commit**

---

### Task 6: Example app

**Files:**
- Create: `examples/fastapi_middleware.py`

```python
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
```

**Commit:** `docs: add fastapi middleware example`

---

### Task 7: Documentation

**Files:**
- Create: `docs/how-to/fastapi.md`
- Modify: `mkdocs.yml` (add nav entry under How-to)

Content outline:

1. Install: `pip install codecarbon[fastapi]`
2. One-liner `add_codecarbon_middleware(app)`
3. Middleware order note ([request runs outermost-first](https://fastapi.tiangolo.com/tutorial/middleware/))
4. `tracking_mode` comparison table
5. Lifespan pattern for `app` mode
6. `exclude_paths`, custom `task_name_formatter`, `on_request_complete` callback
7. **Response headers:** presets (`"emissions"`, `"default"`, `"energy"`, `"power"`, `"full"`), field lists, rename maps, `header_formatter` callback; CORS `expose_headers` for browser clients
8. Limitations: WebSockets not covered in v1; background tasks run after middleware returns
9. Link to `@track_emissions` for single-endpoint use

**Commit:** `docs: add fastapi middleware how-to`

---

### Task 8: Dogfood on carbonserver (optional follow-up)

**Not required for v1 library release.** Separate PR can add middleware to `carbonserver/main.py` behind an env flag:

```python
if settings.enable_emissions_middleware:
    add_codecarbon_middleware(server, project_name="carbonserver-api", exclude_paths={"/health", "/docs"})
```

Keeps API backend changes decoupled from library shipping.

---

## Testing checklist

| Test | Command |
|------|---------|
| Unit: routing helpers | `uv run pytest tests/integrations/test_fastapi_routing.py -v` |
| Unit: response headers | `uv run pytest tests/integrations/test_fastapi_headers.py -v` |
| Unit: middleware (mocked tracker) | `uv run pytest tests/integrations/test_fastapi_middleware.py -v` |
| Unit: lifespan | `uv run pytest tests/integrations/test_fastapi_lifespan.py -v` |
| Import guard | `uv run pytest tests/integrations/test_fastapi_import.py -v` |
| Full package regression | `uv run task test-package` |
| Manual smoke | `uv run --extra fastapi uvicorn examples.fastapi_middleware:app --reload` then `curl -i localhost:8000/predict` |

---

## Middleware order guidance (for docs)

When adding alongside CORS/session middleware:

```python
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(SessionMiddleware, ...)
add_codecarbon_middleware(app)  # added last → outermost on request path
```

Per [FastAPI middleware stacking](https://fastapi.tiangolo.com/tutorial/middleware/): last added = outermost = runs first on request. CodeCarbon should wrap the app so it measures work done by inner middleware and route handlers.

---

## Future enhancements (out of scope for v1)

- WebSocket middleware / connection-level tracking
- Concurrent `start_task` without lock (core tracker change)
- Prometheus labels per route via `save_to_prometheus=True` + custom metric labels
- OpenTelemetry span integration
- Auto-discover OpenAPI `operation_id` as task name

---

## Estimated effort

| Task | Time |
|------|------|
| 1–2 Skeleton + routing | ~30 min |
| 2b Response headers | ~30 min |
| 3 Middleware core | ~1 h |
| 4 Lifespan | ~20 min |
| 5 Import guard | ~15 min |
| 6–7 Example + docs | ~45 min |
| **Total** | **~3.5 h** |
