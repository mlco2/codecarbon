import unittest

from codecarbon.core.units import Energy


class TestEnergy(unittest.TestCase):
    def test_gt(self):
        # WHEN

        e10 = Energy(10)
        e100 = Energy(100)

        # THEN
        self.assertGreater(e100, e10)
