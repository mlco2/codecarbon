import unittest
from unittest import mock

from codecarbon.core.schedulers import JOB_METADATA_FIELDS, detect_job_metadata

SLURM_ENV = {
    "SLURM_JOB_ID": "1234567",
    "SLURM_JOB_NAME": "train",
    "SLURM_JOB_USER": "researcher",
    "SLURM_JOB_ACCOUNT": "proj42",
    "SLURM_JOB_PARTITION": "gpu",
    "SLURMD_NODENAME": "nid001",
}


class TestSchedulers(unittest.TestCase):
    @mock.patch.dict("os.environ", SLURM_ENV, clear=True)
    def test_detect_slurm_env_parses_variables(self):
        self.assertEqual(
            detect_job_metadata(),
            {
                "scheduler": "slurm",
                "job_id": "1234567",
                "job_name": "train",
                "job_user": "researcher",
                "job_account": "proj42",
                "job_partition": "gpu",
                "node_name": "nid001",
            },
        )

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_no_scheduler_env_is_inert(self):
        metadata = detect_job_metadata()
        self.assertEqual(set(metadata), set(JOB_METADATA_FIELDS))
        self.assertEqual(set(metadata.values()), {""})

    @mock.patch.dict("os.environ", {"SLURM_JOB_ID": "42"}, clear=True)
    def test_partial_slurm_env_leaves_others_empty(self):
        metadata = detect_job_metadata()
        self.assertEqual(metadata["scheduler"], "slurm")
        self.assertEqual(metadata["job_id"], "42")
        self.assertEqual(metadata["job_name"], "")

    @mock.patch.dict(
        "os.environ",
        {"CODECARBON_SCHEDULER": "pbs", "CODECARBON_JOB_ID": "99.pbsserver"},
        clear=True,
    )
    def test_generic_env_contract_without_slurm(self):
        metadata = detect_job_metadata()
        self.assertEqual(metadata["scheduler"], "pbs")
        self.assertEqual(metadata["job_id"], "99.pbsserver")

    @mock.patch.dict(
        "os.environ", dict(SLURM_ENV, CODECARBON_JOB_ACCOUNT="billed-to"), clear=True
    )
    def test_generic_env_contract_overrides_slurm(self):
        metadata = detect_job_metadata()
        self.assertEqual(metadata["job_account"], "billed-to")
        self.assertEqual(metadata["job_id"], "1234567")


class TestSchedulerMetadataOnEmissionsData(unittest.TestCase):
    @mock.patch.dict("os.environ", SLURM_ENV, clear=True)
    def test_job_fields_reach_the_emissions_data(self):
        from codecarbon.emissions_tracker import OfflineEmissionsTracker

        tracker = OfflineEmissionsTracker(
            country_iso_code="FRA", output_methods=[], allow_multiple_runs=True
        )
        tracker.start()
        try:
            data = tracker._prepare_emissions_data()
        finally:
            tracker.stop()

        self.assertEqual(data.scheduler, "slurm")
        self.assertEqual(data.job_id, "1234567")
        self.assertEqual(data.job_account, "proj42")
        self.assertEqual(data.node_name, "nid001")
        # The new fields must be part of the CSV columns.
        self.assertIn("job_partition", data.values)
