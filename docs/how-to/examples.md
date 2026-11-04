# CodeCarbon Examples

The directory [examples/](https://github.com/mlco2/codecarbon/tree/master/examples) contains practical examples demonstrating how to use CodeCarbon to track carbon emissions from your computing tasks.

The canonical, always-up-to-date index of every example lives in
[examples/README.md](https://github.com/mlco2/codecarbon/blob/master/examples/README.md),
grouped by use case: getting started, tracking parts of a run, models and
inference, sending results somewhere, configuration, hardware debugging and
clusters. It is not duplicated here so the two cannot drift apart.

## Running the Examples

### Prerequisites
```bash
# Install CodeCarbon
pip install codecarbon

# Install example dependencies
# WARNING: it will download huge pacakge. We recommand you to install only the minimum you need for the example you want to run.
pip install -r examples/requirements-examples.txt
```

### Run a Python Example
```bash
# Using uv (recommended)
uv run examples/print_hardware.py

# Or with Python directly
python examples/print_hardware.py
```

### Run a Jupyter Notebook
```bash
jupyter notebook examples/notebook.ipynb
```

Or just open it in VS Code.

## Common Patterns

### Track with Decorator
```python
from codecarbon import track_emissions

@track_emissions(project_name="my_project")
def my_function():
    # Your code here
    pass
```

### Track with Context Manager
```python
from codecarbon import EmissionsTracker

with EmissionsTracker() as tracker:
    # Your code here
    pass
```

### Track Specific Tasks
```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()
tracker.start_task("data_loading")
# Load data...
tracker.stop_task()

tracker.start_task("training")
# Train model...
tracker.stop_task()
tracker.stop()
```

### Track FastAPI Requests

One tracker runs for the app lifetime; the middleware splits each of its
sampling windows across the requests that were in flight during that window,
weighted by overlap. Per-request start/stop snapshots cannot be used here:
with N requests in flight each one would see the whole machine's delta, so
the sum overcounts by roughly N.

Install the extra with `pip install 'codecarbon[fastapi]'`. Add the middleware
at module level (Starlette refuses new middleware once the app has started),
and start and stop the tracker in the lifespan:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codecarbon import EmissionsTracker
from codecarbon.integrations.fastapi import CodeCarbonMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    tracker = EmissionsTracker(allow_multiple_runs=True)
    tracker.start()
    app.state.codecarbon_tracker = tracker
    yield
    tracker.stop()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CodeCarbonMiddleware)
```

Requests are only recorded while the tracker is running. Anything still
pending is reported when the app shuts down. A request's share is only known
one or more sampling windows *after* its response was sent, so the
`on_request(energy, emissions_kg, status_code)` callback fires then, on the
tracker's scheduler thread — keep it cheap. The default callback logs at DEBUG.
`energy.energy_kwh` is `None` only when the request never overlapped a
completed sampling window, which in practice means it was still pending when
the tracker stopped.

`energy_kwh` is an estimated share, not a measurement of the request. The
whole machine's energy for a window, idle power included, is split across the
requests in flight by how long each overlapped the window. Time spent waiting
on I/O counts the same as time spent computing, and a lone short request in an
otherwise idle window receives that window's full energy. Sum the values per
route over many requests rather than reading a single one, and lower
`measure_power_secs` for finer-grained windows.

With `uvicorn --workers N` (or any multi-process server), each worker gets
its own tracker in its own process, and by default a tracker measures the
*whole machine*. Summing per-request energy across all workers then
overcounts by roughly N×, the same overcounting the middleware avoids within
a single process. Run a single worker per machine when you need per-request
numbers. `tracking_mode="process"` only helps when CPU power is estimated
from CPU load: RAPL, powermetrics and NVML counters are machine-wide, so each
worker still sees the whole machine's energy.
