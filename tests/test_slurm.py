import unittest
from unittest import mock

from codecarbon.core.slurm import warn_on_multi_rank_double_counting
from codecarbon.emissions_tracker import OfflineEmissionsTracker


class TestMultiRankWarning(unittest.TestCase):
    def _warnings(self, tracking_mode="machine", **env):
        with mock.patch.dict("os.environ", env, clear=True):
            with mock.patch("codecarbon.core.slurm.logger") as mocked_logger:
                warn_on_multi_rank_double_counting(tracking_mode)
        return mocked_logger.warning.call_count

    def test_non_zero_local_rank_in_machine_mode_warns(self):
        self.assertEqual(
            1, self._warnings(SLURM_LOCALID="1", SLURM_STEP_TASKS_PER_NODE="4")
        )
        # Heterogeneous allocations are written "4(x2)"; falls back to the job var.
        self.assertEqual(
            1, self._warnings(SLURM_LOCALID="3", SLURM_TASKS_PER_NODE="4(x2)")
        )

    def test_no_warning_without_double_counting(self):
        # Local rank 0 is the recommended tracker.
        self.assertEqual(
            0, self._warnings(SLURM_LOCALID="0", SLURM_STEP_TASKS_PER_NODE="4")
        )
        # Batch step: per-node counts are exported but SLURM_LOCALID is not.
        self.assertEqual(
            0, self._warnings(SLURM_NTASKS_PER_NODE="4", SLURM_TASKS_PER_NODE="4")
        )
        self.assertEqual(0, self._warnings())
        self.assertEqual(0, self._warnings(tracking_mode="process", SLURM_LOCALID="1"))

    def test_tracker_init_warns_on_non_zero_local_rank(self):
        with mock.patch.dict("os.environ", {"SLURM_LOCALID": "2"}):
            with mock.patch("codecarbon.core.slurm.logger") as mocked_logger:
                OfflineEmissionsTracker(country_iso_code="FRA", tracking_mode="machine")
        self.assertEqual(1, mocked_logger.warning.call_count)
