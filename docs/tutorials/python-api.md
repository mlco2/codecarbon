# Tracking with Python

CodeCarbon can be used along with any computing framework. It
supports both `online` (with internet access) and `offline` (without
internet access) modes.

## Online Mode

When the environment has internet access, the `EmissionsTracker` object
or the `track_emissions` decorator can be used, which has the `offline`
parameter set to `False` by default.

### Explicit Object

In the case of absence of a single entry and stop point for the training
code base, users can instantiate a `EmissionsTracker` object and pass it
as a parameter to function calls to start and stop the emissions
tracking of the compute section.

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

This mode is recommended when using a Jupyter Notebook. You call
`tracker.start()` at the beginning of the Notebook, and call
`tracker.stop()` in the last cell.

This mode also allows you to record the monitoring with
`tracker.flush()` that writes the emissions to disk or call the API
depending on the configuration, but keep running the experiment.

If you want to monitor small piece of code, like a model inference, you
could use the task manager:

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

This way CodeCarbon will track the emissions of each task . The task
will not be written to disk to prevent overhead, you have to get the
results from the return of `stop_task()`. If no name is provided,
CodeCarbon will generate a uuid.

Please note that you can't use task mode and normal mode at the same
time. Because `start_task` will stop the scheduler as we do not want it
to interfere with the task measurement.

### Context manager

The `Emissions tracker` also works as a context manager.

``` python
from codecarbon import EmissionsTracker

with EmissionsTracker() as tracker:
    # Compute intensive training code goes here
```

This mode is recommended when you want to monitor a specific block of
code.

### Decorator

In case the training code base is wrapped in a function, users can use
the decorator `@track_emissions` within the function to enable tracking
emissions of the training code.

``` python
from codecarbon import track_emissions

@track_emissions
def training_loop():
    # Compute intensive training code goes here
```

This mode is recommended if you have a training function.

!!! note "Note"

    This will write a csv file named emissions.csv in the current directory.

## Offline Mode

An offline version is available to support restricted environments
without internet access. The internal computations remain unchanged;
however, a `country_iso_code` parameter, which corresponds to the
3-letter alphabet ISO Code of the country where the compute
infrastructure is hosted, is required to fetch Carbon Intensity details
of the regional electricity used. A complete list of country ISO codes
can be found on
[Wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes).

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

### Context manager

The `OfflineEmissionsTracker` also works as a context manager

``` python
from codecarbon import OfflineEmissionsTracker

with OfflineEmissionsTracker() as tracker:
# GPU intensive training code  goes here
```

### Decorator

The `track_emissions` decorator in offline mode requires following two
parameters:

-   `offline` needs to be set to `True`, which defaults to `False` for
    online mode.
-   `country_iso_code` the 3-letter alphabet ISO Code of the country
    where the compute infrastructure is hosted

```python
from codecarbon import track_emissions
@track_emissions(offline=True, country_iso_code="CAN")
def training_loop():
    # training code goes here
    pass
```

The Carbon emissions will be saved to a `emissions.csv` file in the same
directory. Please refer to the
[API Reference](../reference/api.md) for additional
parameters and configuration options.
