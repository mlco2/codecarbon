import os.path
import unittest
from os import path

from codecarbon.core.rapl import RAPLFile
from codecarbon.core.units import Energy, Time


class TestEnergy(unittest.TestCase):
    def setUp(self):
        self.mock_energy_data_filename = "mock_rapl_data.txt"
        self.path = path.join(
            path.dirname(os.path.abspath(__file__)), "test_data/mock_rapl_data.txt"
        )
        self.max_path = path.join(
            path.dirname(os.path.abspath(__file__)), "test_data/mock_rapl_data_max.txt"
        )

        # Setup the RAPL File with a high energy level
        with open(self.path, "w") as f:
            f.write("100")
        # Setup the RAPL maximum value to be the energy level where we wrap
        with open(self.max_path, "w") as f:
            f.write("105")

    def test_wraparound_delta_correct_value(self):
        first_rapl_measure = RAPLFile(
            name=self.mock_energy_data_filename, path=self.path, max_path=self.max_path
        )

        # Read the initial state
        first_rapl_measure.start()
        # Write a cumulated value lower than the initial one
        with open(self.path, "w") as f:
            f.write("10")
        # Update state
        first_rapl_measure.delta(Time(seconds=1))

        # Assert the delta has given the correct value from wraparound (reading + max_value - previous_value)
        self.assertAlmostEqual(
            Energy.from_ujoules(15).kWh, first_rapl_measure.energy_delta.kWh
        )
