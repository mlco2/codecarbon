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
