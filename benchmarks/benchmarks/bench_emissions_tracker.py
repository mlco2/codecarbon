TRACKER_SETUP = """
import os
from tempfile import TemporaryDirectory

from codecarbon import OfflineEmissionsTracker

tmpdir = TemporaryDirectory()
home = TemporaryDirectory()
os.environ["HOME"] = home.name
os.chdir(tmpdir.name)
tracker = OfflineEmissionsTracker(
    country_iso_code="FRA",
    output_dir=tmpdir.name,
    output_file="emissions.csv",
    measure_power_secs=3600,
    save_to_file=False,
    allow_multiple_runs=True,
    log_level="critical",
)
"""


class TrackerStartTime:
    """Measure the time it takes to start the tracker."""

    number = 1
    repeat = 5
    timeout = 120

    def timeraw_start(self):
        return "tracker.start()", TRACKER_SETUP


class TrackerStopTime:
    """Measure the time it takes to stop the tracker."""

    number = 1
    repeat = 5
    timeout = 120

    def timeraw_stop(self):
        return "tracker.stop()", TRACKER_SETUP + "\ntracker.start()\n"


class TrackerLifecycleTime:
    """Measure the time it takes to start and stop the tracker.

    This is useful to see if there is some overhead between the start and stop
    of the tracker.
    """

    number = 1
    repeat = 5
    timeout = 120

    def timeraw_lifecycle(self):
        return (
            """
tracker.start()
tracker.stop()
""",
            TRACKER_SETUP,
        )
