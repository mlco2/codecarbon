import inspect
import unittest
from unittest import mock

from codecarbon import emissions_tracker
from codecarbon.emissions_tracker import (
    BaseEmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)

# Parameters of the decorator that are not tracker parameters.
DECORATOR_ONLY = {"fn", "offline"}


def _params(func):
    return set(inspect.signature(func).parameters) - {"self", "args", "kwargs"}


class TestTrackEmissionsDecoratorParity(unittest.TestCase):
    def test_decorator_exposes_every_tracker_parameter(self):
        tracker_params = _params(BaseEmissionsTracker.__init__) | _params(
            OfflineEmissionsTracker.__init__
        )
        decorator_params = _params(track_emissions) - DECORATOR_ONLY

        self.assertEqual(
            tracker_params - decorator_params,
            set(),
            "track_emissions is missing tracker parameters",
        )
        self.assertEqual(
            decorator_params - tracker_params,
            set(),
            "track_emissions has parameters no tracker accepts",
        )

    def _run_decorated(self, tracker_cls_name, **decorator_kwargs):
        with mock.patch.object(emissions_tracker, tracker_cls_name) as tracker_cls:

            @track_emissions(**decorator_kwargs)
            def fn():
                return 42

            self.assertEqual(fn(), 42)
        tracker_cls.return_value.start.assert_called_once()
        tracker_cls.return_value.stop.assert_called_once()
        return tracker_cls.call_args.kwargs

    def test_online_forwards_cpu_modes_and_metadata(self):
        kwargs = self._run_decorated(
            "EmissionsTracker",
            force_mode_cpu_load=True,
            force_mode_constant=True,
            metadata={"team": "green"},
        )
        self.assertIs(kwargs["force_mode_cpu_load"], True)
        self.assertIs(kwargs["force_mode_constant"], True)
        self.assertEqual(kwargs["metadata"], {"team": "green"})

    def test_offline_forwards_cpu_modes_and_metadata(self):
        kwargs = self._run_decorated(
            "OfflineEmissionsTracker",
            offline=True,
            country_iso_code="FRA",
            force_mode_cpu_load=True,
            force_mode_constant=True,
            metadata={"team": "green"},
        )
        self.assertIs(kwargs["force_mode_cpu_load"], True)
        self.assertIs(kwargs["force_mode_constant"], True)
        self.assertEqual(kwargs["metadata"], {"team": "green"})
