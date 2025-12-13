import os
import subprocess as sp
import tempfile
import time
import unittest

from codecarbon.emissions_tracker import OfflineEmissionsTracker

python_load_code = """
import math
i = 0
erg = 0
while True:
    i += 1
    a = math.sqrt(64*64*64*64*64)
    erg += a
print(erg)
"""


class TestPIDTracking(unittest.TestCase):
    def setUp(self) -> None:
        self.project_name = "project_TestPIDTracking"
        self.emissions_file = "emissions-test-TestPIDTracking"
        self.emissions_path = tempfile.gettempdir()
        self.emissions_file_path = os.path.join(
            self.emissions_path, self.emissions_file
        )
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

        self.pids = []
        self.process = []
        for _ in range(128):
            self.process.append(sp.Popen(["python", "-c", python_load_code]))
            self.pids.append(self.process[-1].pid)
        self.pids.append(os.getpid())

    def tearDown(self) -> None:
        if os.path.isfile(self.emissions_file_path):
            os.remove(self.emissions_file_path)

        for proc in self.process:
            proc.terminate()
            proc.wait()

    def test_carbon_pid_tracking_offline(self):

        # Subprocess PIDs are children, therefore both should be equal
        tracker_pid = OfflineEmissionsTracker(
            output_dir=self.emissions_path,
            output_file=self.emissions_file + "_pid.csv",
            tracking_mode="process",
            tracking_pids=self.pids,
        )
        tracker_self = OfflineEmissionsTracker(
            output_dir=self.emissions_path,
            output_file=self.emissions_file + "_global.csv",
            tracking_mode="process",
            tracking_pids=[os.getpid()],
        )

        tracker_pid.start()
        tracker_self.start()

        time.sleep(5)

        emissions_pid = tracker_pid.stop()
        emissions_self = tracker_self.stop()

        print(f"Emissions (self): {emissions_self} kgCO2eq")
        print(f"Emissions (pid): {emissions_pid} kgCO2eq")

        if not isinstance(emissions_pid, float):
            print(emissions_pid)
        assert isinstance(emissions_pid, float)

        self.assertNotEqual(emissions_pid, 0.0)

        # Compare emissions from both trackers, should be less than 10% difference
        diff = abs(emissions_pid - emissions_self)
        avg = (emissions_pid + emissions_self) / 2
        percent_diff = (diff / avg) * 100
        print(f"Percent difference: {percent_diff}%")
        self.assertLessEqual(percent_diff, 10.0)
