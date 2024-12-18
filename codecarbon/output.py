"""
Provides functionality for persistence of data
"""

from codecarbon.output_methods.base_output import BaseOutput  # noqa: F401

# emissions data
from codecarbon.output_methods.emissions_data import (  # noqa: F401
    EmissionsData,
    TaskEmissionsData,
)

# Output to a file
from codecarbon.output_methods.file import FileOutput  # noqa: F401

# Output calling a REST http endpoint
from codecarbon.output_methods.http import CodeCarbonAPIOutput, HTTPOutput  # noqa: F401

# Output to a logger
from codecarbon.output_methods.logger import (  # noqa: F401
    GoogleCloudLoggerOutput,
    LoggerOutput,
)
from codecarbon.output_methods.metrics.logfire import LogfireOutput  # noqa: F401

# output is sent to metrics
from codecarbon.output_methods.metrics.prometheus import PrometheusOutput  # noqa: F401
