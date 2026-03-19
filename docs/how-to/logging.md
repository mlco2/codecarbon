# Log to External Systems {#logging}

CodeCarbon provides the `LoggerOutput` class to send emissions tracking data to external logging systems. This allows you to integrate CodeCarbon emissions data with your existing monitoring and logging infrastructure, enabling centralized tracking, reporting, and alerting.

The `LoggerOutput` class (and `GoogleCloudLoggerOutput` subclass) works independently from CodeCarbon's internal logging, allowing you to leverage powerful logging systems and build automated reports or triggers based on emissions data.

## Overview

This guide shows how to integrate CodeCarbon with:

- **Python's built-in logging system** (local file or stream)
- **Google Cloud Logging** (cloud-based centralized logging)

## Setup Steps

### Step 1: Create a Logger

In order to send emissions tracking data to the logger, first create a logger and then create an `EmissionsTracker`. `OfflineEmissionsTracker` is also supported but lack of network connectivity may forbid to stream tracking data to some central or cloud-based collector.

#### Option 1: Python Logger (Local File)

Create a logger that writes to a local file:

``` python
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

#### Option 2: Google Cloud Logging (Cloud-Based)

Send emissions data to Google Cloud Logging for centralized cloud-based tracking:

``` python
import google.cloud.logging


# Create a Cloud Logging client (specify project name if needed, otherwise Google SDK default project name is used)
client = google.cloud.logging.Client(project=google_project_name)

# Create a CodeCarbon GoogleCloudLoggerOutput with the Cloud Logging logger, with the logging level to be used for emissions data messages
my_logger = GoogleCloudLoggerOutput(client.logger(log_name))
```

#### Google Cloud Authentication

For Google Cloud Logging setup, refer to [Google Cloud documentation](https://cloud.google.com/logging/docs/reference/libraries#setting_up_authentication) for authentication configuration.

### Step 2: Create an EmissionsTracker

Create an EmissionsTracker that sends output to your logger. Other save options can be used simultaneously:

``` python
tracker = EmissionsTracker(save_to_logger=True, logging_logger=my_logger)
tracker.start()
# Your code here
emissions: float = tracker.stop()
```

## Complete Examples

A full working example is available in `codecarbon/examples/logging_demo.py`.

## Next Steps

- [Send emissions data to the cloud](cloud-api.md) for dashboard visualization
- [Integrate with Comet](comet.md) for experiment tracking
- [Configure CodeCarbon](configuration.md) to customize logging behavior
