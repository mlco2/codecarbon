import os.path
import unittest
from os import path

from core.rapl import RAPLFile

from codecarbon.core.units import Energy, Time


class TestEnergy(unittest.TestCase):
    def setUp(self):
        self.mock_energy_data_filename = "mock_rapl_data.txt"
        self.path = path.join(
            path.dirname(os.path.abspath(__file__)), "test_data/mock_rapl_data.txt"
        )

        # Setup the RAPL File with a high energy level
        with open(self.path, "w") as f:
            f.write("100")

    def test_negative_delta_writes_no_delta(self):
        first_rapl_measure = RAPLFile(
            name=self.mock_energy_data_filename, path=self.path
        )

        # Write a cumulated value lower than the initial one
        with open(self.path, "w") as f:
            f.write("10")
        first_rapl_measure.delta(Time(seconds=1))

        # Assert the delta didn't write a negative delta value
        self.assertEqual(Energy(0), first_rapl_measure.energy_delta)
