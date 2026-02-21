# Collecting emissions to a logger {#Collecting emissions to a logger}

The `LoggerOutput` class (and `GoogleCloudLoggerOutput` subclass) allows
to send emissions tracking to a logger. This is a specific, distinct
logger than the one used by the CodeCarbon package for its \'private\'
logs. It allows to leverage powerful logging systems, to centralize
emissions to some central or cloud-based system, and build reports,
triggers, etc. based on these data.

This logging output can be used in parallel with other output options
provided by CodeCarbon.

## Create a logger

In order to send emissions tracking data to the logger, first create a
logger and then create an [EmissionTracker]{.title-ref}.
[OfflineEmissionTracker]{.title-ref} is also supported but lack of
network connectivity may forbid to stream tracking data to some central
or cloud-based collector.

### Python logger

``` Python
import logging

# Create a dedicated logger (log name can be the CodeCarbon project name for example)
_logger = logging.getLogger(log_name)

# Add a handler, see Python logging for various handlers (here a local file named after log_name)
_channel = logging.FileHandler(log_name + '.log')
_logger.addHandler(_channel)

# Set logging level from DEBUG to CRITICAL (typically INFO)
# This level can be used in the logging process to filter emissions messages
_logger.setLevel(logging.INFO)

# Create a CodeCarbon LoggerOutput with the logger, specifying the logging level to be used for emissions data messages
my_logger = LoggerOutput(_logger, logging.INFO)
```

### Google Cloud Logging

``` Python
import google.cloud.logging


# Create a Cloud Logging client (specify project name if needed, otherwise Google SDK default project name is used)
client = google.cloud.logging.Client(project=google_project_name)

# Create a CodeCarbon GoogleCloudLoggerOutput with the Cloud Logging logger, with the logging level to be used for emissions data messages
my_logger = GoogleCloudLoggerOutput(client.logger(log_name))
```

### Authentication

Please refer to [Google Cloud
documentation](https://cloud.google.com/logging/docs/reference/libraries#setting_up_authentication).

### Create an EmissionTracker

Create an EmissionTracker saving output to the logger. Other save
options are still usable and valid.

``` Python
tracker = EmissionsTracker(save_to_logger=True, logging_logger=my_logger)
tracker.start()
...
emissions: float = tracker.stop()
...
```

### Example

A demonstration is available in `codecarbon/examples/logging_demo.py`.
