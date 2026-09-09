import unittest
from unittest import mock

from codecarbon.core.slurm import warn_on_multi_rank_double_counting


class TestMultiRankWarning(unittest.TestCase):
    def _warnings(self, tracking_mode="machine", **env):
        with mock.patch.dict("os.environ", env, clear=True):
            with mock.patch("codecarbon.core.slurm.logger") as mocked_logger:
                warn_on_multi_rank_double_counting(tracking_mode)
        return mocked_logger.warning.call_count

    def test_several_ranks_per_node_in_machine_mode_warns(self):
        self.assertEqual(1, self._warnings(SLURM_NTASKS_PER_NODE="4"))
        # Heterogeneous allocations are written "4(x2)".
        self.assertEqual(1, self._warnings(SLURM_NTASKS_PER_NODE="4(x2)"))

    def test_no_warning_without_double_counting(self):
        self.assertEqual(0, self._warnings(SLURM_NTASKS_PER_NODE="1"))
        self.assertEqual(0, self._warnings())
        self.assertEqual(
            0, self._warnings(tracking_mode="process", SLURM_NTASKS_PER_NODE="4")
        )
