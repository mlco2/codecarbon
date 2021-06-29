import unittest

import numpy as np

from codecarbon.external.hardware import RAM

# TODO: need help: test multiprocess case


class TestRAM(unittest.TestCase):
    def test_ram_diff(self):
        ram = RAM()

        for array_size in [
            # (10, 10),  # too small to be noticed
            # (100, 100),  # too small to be noticed
            (1000, 1000),  # ref for atol
            (10, 1000, 1000),
            (20, 1000, 1000),
            (100, 1000, 1000),
            (200, 1000, 1000),
            (1000, 1000, 1000),
            (2000, 1000, 1000),
        ]:
            with self.subTest(array_size=array_size):
                ref_W = ram.total_power().W
                array = np.ones(array_size, dtype=np.int8)
                new_W = ram.total_power().W
                n_gb = array.nbytes / (1000 ** 3)
                n_gb_W = (new_W - ref_W) / ram.power_per_GB
                is_close = np.isclose(n_gb, n_gb_W, atol=1e-3)
                self.assertTrue(
                    is_close,
                    msg=f"{array_size}, {n_gb}, {n_gb_W}, {is_close}",
                )
                del array
