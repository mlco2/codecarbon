import random
from typing import Iterable

import logfire
from opentelemetry.metrics import CallbackOptions, Observation

from codecarbon.core.emissions import Emissions
from tests.testutils import get_test_data_source


def temperature_callback(options: CallbackOptions) -> Iterable[Observation]:
    for room in ["kitchen", "living_room", "bedroom"]:
        temperature = random.randint(18, 30)
        yield Observation(temperature, {"room": room})


def test_codecarbon_pushes_2_emission_data_to_logfire_dashboard():
    # GIVEN:
    data_source = get_test_data_source()
    Emissions(data_source)
    # WHEN:
    logfire.metric_gauge_callback(
        "temperature",
        unit="C",
        callbacks=[temperature_callback],
        description="Temperature",
    )

    # THEN:
    assert 0 == 1


if __name__ == "__main__":
    test_codecarbon_pushes_2_emission_data_to_logfire_dashboard()
