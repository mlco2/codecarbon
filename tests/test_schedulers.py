import unittest
from unittest import mock

from codecarbon.core.schedulers import detect_scheduler_job_id


class TestSchedulers(unittest.TestCase):
    @mock.patch.dict("os.environ", {"SLURM_JOB_ID": "1234567"}, clear=True)
    def test_slurm_job_id_is_detected(self):
        self.assertEqual("1234567", detect_scheduler_job_id())

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_no_scheduler_env_is_inert(self):
        self.assertEqual("", detect_scheduler_job_id())

    @mock.patch.dict(
        "os.environ", {"CODECARBON_SCHEDULER_JOB_ID": "99.pbsserver"}, clear=True
    )
    def test_generic_env_contract_without_slurm(self):
        self.assertEqual("99.pbsserver", detect_scheduler_job_id())

    @mock.patch.dict(
        "os.environ",
        {"SLURM_JOB_ID": "1234567", "CODECARBON_SCHEDULER_JOB_ID": "override"},
        clear=True,
    )
    def test_generic_env_contract_overrides_slurm(self):
        self.assertEqual("override", detect_scheduler_job_id())


class TestSchedulerJobIdOnEmissionsData(unittest.TestCase):
    @mock.patch.dict("os.environ", {"SLURM_JOB_ID": "1234567"}, clear=True)
    def test_job_id_reaches_the_emissions_data(self):
        from codecarbon.emissions_tracker import OfflineEmissionsTracker

        tracker = OfflineEmissionsTracker(
            country_iso_code="FRA", output_methods=[], allow_multiple_runs=True
        )
        tracker.start()
        try:
            data = tracker._prepare_emissions_data()
        finally:
            tracker.stop()

        self.assertEqual("1234567", data.scheduler_job_id)
        # The new field must be part of the CSV columns.
        self.assertIn("scheduler_job_id", data.values)
