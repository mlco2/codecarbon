"""
BoAmps output support for CodeCarbon.

Provides first-class support for generating BoAmps (Boavizta) standardized
JSON reports from CodeCarbon emission tracking data.
"""

from codecarbon.output_methods.boamps.mapper import (  # noqa: F401
    map_emissions_to_boamps,
)
from codecarbon.output_methods.boamps.models import (  # noqa: F401
    BoAmpsAlgorithm,
    BoAmpsDataset,
    BoAmpsEnvironment,
    BoAmpsHardware,
    BoAmpsHeader,
    BoAmpsInfrastructure,
    BoAmpsMeasure,
    BoAmpsPublisher,
    BoAmpsReport,
    BoAmpsSoftware,
    BoAmpsSystem,
    BoAmpsTask,
)
from codecarbon.output_methods.boamps.output import BoAmpsOutput  # noqa: F401
