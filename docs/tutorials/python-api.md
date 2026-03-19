# Tracking with Python

In this tutorial, you'll learn the three main ways to use CodeCarbon in your Python code. You can use CodeCarbon with any computing framework, and it supports both `online` (with internet access) and `offline` (without internet access) modes.

By the end of this tutorial, you'll understand which usage pattern works best for your use case.

## Online Mode

When the environment has internet access, CodeCarbon will send your emissions data to the central API (optional). Let's start with three usage patterns: explicit object, context manager, and decorator.

### Explicit Object

The explicit object pattern is useful when your code doesn't have a single entry and exit point—for example, in Jupyter notebooks where you want to start tracking in one cell and stop in a much later cell.

``` python
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()
tracker.start()
try:
     # Compute intensive code goes here
     _ = 1 + 1
finally:
     tracker.stop()
```

Call `tracker.start()` at the beginning of your Notebook (or script), and call `tracker.stop()` at the end. You can also call `tracker.flush()` to write emissions to disk or the API without stopping the tracker entirely.

**Advanced: Task-Level Monitoring**

For fine-grained tracking of individual tasks within a single run, use the task manager:

``` python
try:
    tracker = EmissionsTracker(project_name="bert_inference", measure_power_secs=10)
    tracker.start_task("load dataset")
    dataset = load_dataset("imdb", split="test")
    imdb_emissions = tracker.stop_task()
    tracker.start_task("build model")
    model = build_model()
    model_emissions = tracker.stop_task()
finally:
    _ = tracker.stop()
```

The task manager tracks each sub-task independently. Tasks are not written to disk by default (to reduce overhead), so retrieve results from the `stop_task()` return value.

### Context Manager

Now that you've seen the explicit object approach, let's look at the more idiomatic **context manager** pattern. This is the recommended way for most use cases.

``` python
from codecarbon import EmissionsTracker

with EmissionsTracker() as tracker:
    # Compute intensive training code goes here
```

This pattern is recommended when you want to monitor a specific block of code. The context manager automatically calls `start()` on entry and `stop()` on exit, making it safe and concise.

### Decorator

Finally, if your training code is wrapped in a function, you can use the `@track_emissions` decorator for the simplest syntax.

``` python
from codecarbon import track_emissions

@track_emissions
def training_loop():
    # Compute intensive training code goes here
```

The decorator automatically wraps your function with tracking and writes results to `emissions.csv`. Use this when your code is neatly encapsulated in a function.

!!! note
    All patterns create an `emissions.csv` file in your current directory containing detailed tracking data.

## Offline Mode

So far we've assumed an internet connection. CodeCarbon also works fully **offline** without internet access. The internal computations remain unchanged; however, you must provide a `country_iso_code` parameter (3-letter ISO code) so CodeCarbon can estimate the carbon intensity of your regional electricity grid. See [Wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) for a complete list of country codes.

The three usage patterns (explicit object, context manager, decorator) work the same in offline mode:

### Explicit Object

Developers can use the `OfflineEmissionsTracker` object to track
emissions as follows:

``` python
from codecarbon import OfflineEmissionsTracker
tracker = OfflineEmissionsTracker(country_iso_code="CAN")
tracker.start()
# GPU intensive training code
tracker.stop()
```

### Context Manager

The `OfflineEmissionsTracker` also works as a context manager:

``` python
from codecarbon import OfflineEmissionsTracker

with OfflineEmissionsTracker(country_iso_code="CAN") as tracker:
    # GPU intensive training code goes here
```

### Decorator

The decorator in offline mode requires two additional parameters:

``` python
from codecarbon import track_emissions

@track_emissions(offline=True, country_iso_code="CAN")
def training_loop():
    # training code goes here
    pass
```

---

## What's Next?

You've now learned the three main patterns for tracking emissions in Python. Each pattern serves different use cases:

- **Use the explicit object pattern** when your code runs across multiple cells or functions with unclear start/end points (e.g., Jupyter notebooks).
- **Use the context manager pattern** for most new code—it's concise, safe, and idiomatic.
- **Use the decorator pattern** when your entire tracking scope is a single function.
- **Use offline mode** when you're in an environment without internet access.

Explore these related guides:

- [CLI tutorial](cli.md) — Track emissions from any command without writing Python code.
- [Comparing Model Efficiency](comparing-model-efficiency.md) — Measure and compare carbon emissions across different machine learning models.
- [How-to: Cloud API](../how-to/cloud-api.md) — Send emissions data to the CodeCarbon dashboard.
- [API Reference](../reference/api.md) — Complete list of all parameters and configuration options.
