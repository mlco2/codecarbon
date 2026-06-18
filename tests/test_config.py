import os
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent
from unittest import mock
from unittest.mock import patch

from codecarbon.core.config import (
    clean_env_key,
    get_hierarchical_config,
    normalize_gpu_ids,
    parse_env_config,
    parse_gpu_ids,
)
from codecarbon.emissions_tracker import (
    EmissionsTracker,
    OfflineEmissionsTracker,
    track_emissions,
)
from codecarbon.external.hardware import GPU
from tests.testutils import get_custom_mock_open


class TestConfig(unittest.TestCase):
    def setUp(self):
        self._original_environ = os.environ.copy()
        for key in [
            "CODECARBON_API_KEY",
            "CODECARBON_EXPERIMENT_ID",
            "CODECARBON_API_ENDPOINT",
            "CODECARBON_TELEMETRY",
            "CODECARBON_TELEMETRY_PROJECT_TOKEN",
            "codecarbon_api_key",
            "codecarbon_experiment_id",
            "codecarbon_api_endpoint",
            "codecarbon_telemetry",
            "codecarbon_telemetry_project_token",
        ]:
            os.environ.pop(key, None)
        os.environ.setdefault("CODECARBON_ALLOW_MULTIPLE_RUNS", "True")

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_clean_env_key(self):
        for key in [1, None, 0.2, [], set()]:
            with self.assertRaises(AssertionError):
                clean_env_key(key)
        for key, target in [
            ("", ""),
            ("USER", "user"),
            ("CODECARBON_TEST", "test"),
            ("CODECARBON_TEST_VALUE", "test_value"),
            ("CODECARBON_TEST_1", "test_1"),
            ("CODECARBON_1", "1"),
        ]:
            self.assertEqual(clean_env_key(key), target)

    def test_parse_gpu_ids(self):
        for ids, target in [
            ("0,1,2", ["0", "1", "2"]),
            ("[0, 1, 2", ["0", "1", "2"]),
            ("(0, 1, 2)", ["0", "1", "2"]),
            ("[1]", ["1"]),
            ("1", ["1"]),
            ("0", ["0"]),
            ("MIG-f1e", ["MIG-f1e"]),
            ("", []),
            ([], []),
            ([1, 2, 3], ["1", "2", "3"]),
        ]:
            self.assertEqual(parse_gpu_ids(ids), target)

    def test_normalize_gpu_ids(self):
        for ids, target in [
            (None, None),
            ("0,1,2", ["0", "1", "2"]),
            ("MIG-f1e$%^", ["MIG-f1e"]),
            ([1, 2, 3], [1, 2, 3]),
            (
                [0, "MIG-f1e$%^", "1, 2", "GPU-abcd!"],
                [0, "MIG-f1e", "1", "2", "GPU-abcd"],
            ),
            ([0, {"invalid": "entry"}, "GPU-123"], [0, "GPU-123"]),
        ]:
            self.assertEqual(normalize_gpu_ids(ids), target)

    @mock.patch.dict(
        os.environ,
        {
            "USER": "yes",
            "CODECARBON_TEST": "test-VALUE",
            "CODECARBON_TEST_KEY": "this_other_value",
        },
    )
    def test_parse_env_config(self):
        self.assertDictEqual(
            parse_env_config(),
            {
                "codecarbon": {
                    "allow_multiple_runs": "True",
                    "test": "test-VALUE",
                    "test_key": "this_other_value",
                }
            },
        )

    def test_read_confs(self):
        global_conf = dedent(
            """\
            [codecarbon]
            no_overwrite=path/to/somewhere
            local_overwrite=ERROR:not overwritten
            syntax_test_key= no/space= problem2
            """
        )
        local_conf = dedent(
            """\
            [codecarbon]
            local_overwrite=SUCCESS:overwritten
            local_new_key=cool value
            """
        )

        with patch(
            "builtins.open", new_callable=get_custom_mock_open(global_conf, local_conf)
        ):
            conf = dict(get_hierarchical_config())
            target = {
                "allow_multiple_runs": "True",
                "no_overwrite": "path/to/somewhere",
                "local_overwrite": "SUCCESS:overwritten",
                "syntax_test_key": "no/space= problem2",
                "local_new_key": "cool value",
            }
            self.assertDictEqual(conf, target)

    def test_get_hierarchical_config_logs_debug_for_global_and_local_files(self):
        with (
            tempfile.TemporaryDirectory() as home_dir,
            tempfile.TemporaryDirectory() as cwd_dir,
        ):
            home_cfg = Path(home_dir) / ".codecarbon.config"
            local_cfg = Path(cwd_dir) / ".codecarbon.config"
            home_cfg.write_text("[codecarbon]\nglobal_key=1\n", encoding="utf-8")
            local_cfg.write_text("[codecarbon]\nlocal_key=2\n", encoding="utf-8")

            with (
                patch("codecarbon.core.config.Path.home", return_value=Path(home_dir)),
                patch("codecarbon.core.config.Path.cwd", return_value=Path(cwd_dir)),
                self.assertLogs("codecarbon", level="DEBUG") as logs,
            ):
                get_hierarchical_config()

            messages = "\n".join(logs.output)
            self.assertIn("global file", messages)
            self.assertIn("local file", messages)

    def test_get_hierarchical_config_logs_debug_for_local_file_only(self):
        with tempfile.TemporaryDirectory() as cwd_dir:
            local_cfg = Path(cwd_dir) / ".codecarbon.config"
            local_cfg.write_text("[codecarbon]\nlocal_key=2\n", encoding="utf-8")

            with (
                patch(
                    "codecarbon.core.config.Path.home",
                    return_value=Path("/nonexistent-home"),
                ),
                patch("codecarbon.core.config.Path.cwd", return_value=Path(cwd_dir)),
                self.assertLogs("codecarbon", level="DEBUG") as logs,
            ):
                get_hierarchical_config()

            messages = "\n".join(logs.output)
            self.assertIn("local file", messages)

    @mock.patch.dict(
        os.environ,
        {
            "USER": "useless key",
            "CODECARBON_ENV_OVERWRITE": "SUCCESS:overwritten",
            "CODECARBON_ENV_NEW_KEY": "cool value",
            "CODECARBON_ALLOW_MULTIPLE_RUNS": "True",
        },
    )
    def test_read_confs_and_parse_envs(self):
        global_conf = dedent(
            """\
            [codecarbon]
            no_overwrite=path/to/somewhere
            local_overwrite=ERROR:not overwritten
            syntax_test_key= no/space= problem2
            env_overwrite=ERROR:not overwritten
            """
        )
        local_conf = dedent(
            """\
            [codecarbon]
            local_overwrite=SUCCESS:overwritten
            local_new_key=cool value
            env_overwrite=ERROR:not overwritten
            """
        )

        with patch(
            "builtins.open", new_callable=get_custom_mock_open(global_conf, local_conf)
        ):
            conf = dict(get_hierarchical_config())
            target = {
                "allow_multiple_runs": "True",
                "no_overwrite": "path/to/somewhere",
                "local_overwrite": "SUCCESS:overwritten",
                "env_overwrite": "SUCCESS:overwritten",
                "syntax_test_key": "no/space= problem2",
                "local_new_key": "cool value",
                "env_new_key": "cool value",
            }
            self.assertDictEqual(conf, target)

    def test_empty_conf(self):
        global_conf = ""
        local_conf = ""

        with patch(
            "builtins.open", new_callable=get_custom_mock_open(global_conf, local_conf)
        ):
            conf = dict(get_hierarchical_config())
            # allow_multiple_runs is set in pytest.ini and not mocked, so it's visible here.
            target = {"allow_multiple_runs": "True"}
            self.assertDictEqual(conf, target)

    @mock.patch.dict(
        os.environ,
        {
            "CODECARBON_SAVE_TO_FILE": "true",
            "CODECARBON_GPU_IDS": "0, 1",
            "CODECARBON_PROJECT_NAME": "ERROR:not overwritten",
        },
    )
    def test_full_hierarchy(self):
        global_conf = dedent(
            """\
            [codecarbon]
            measure_power_secs=10
            force_cpu_power=toto
            force_ram_power=50.5
            output_dir=ERROR:not overwritten
            save_to_file=ERROR:not overwritten
            force_carbon_intensity_g_co2e_kwh=123.4
            """
        )
        local_conf = dedent(
            """\
            [codecarbon]
            output_dir=/success/overwritten
            emissions_endpoint=http://testhost:2000
            gpu_ids=ERROR:not overwritten
            """
        )

        with patch(
            "builtins.open", new_callable=get_custom_mock_open(global_conf, local_conf)
        ):
            with patch("os.path.exists", return_value=True):
                tracker = EmissionsTracker(
                    project_name="test-project",
                    electricitymaps_api_token="signal-token",
                )
            self.assertEqual(tracker._measure_power_secs, 10)
            self.assertEqual(tracker._force_cpu_power, None)
            self.assertEqual(tracker._force_ram_power, 50.5)
            self.assertEqual(tracker._output_dir, "/success/overwritten")
            self.assertEqual(tracker._emissions_endpoint, "http://testhost:2000")
            self.assertEqual(tracker._gpu_ids, ["0", "1"])
            self.assertEqual(tracker._electricitymaps_api_token, "signal-token")
            self.assertEqual(tracker.force_carbon_intensity_g_co2e_kwh, 123.4)
            self.assertEqual(tracker._project_name, "test-project")
            self.assertTrue(tracker._save_to_file)

    def test_force_carbon_intensity_constructor_overrides_config(self):
        global_conf = dedent(
            """\
            [codecarbon]
            force_carbon_intensity_g_co2e_kwh=123.4
            """
        )

        with patch("builtins.open", new_callable=get_custom_mock_open(global_conf, "")):
            with patch("os.path.exists", return_value=True):
                tracker = EmissionsTracker(
                    force_carbon_intensity_g_co2e_kwh=456.7,
                    save_to_file=False,
                    allow_multiple_runs=True,
                )

        self.assertEqual(tracker.force_carbon_intensity_g_co2e_kwh, 456.7)
        self.assertEqual(tracker._conf["force_carbon_intensity_g_co2e_kwh"], 456.7)

    def test_offline_tracker_accepts_force_carbon_intensity_parameter(self):
        with patch("builtins.open", new_callable=get_custom_mock_open("", "")):
            with patch("os.path.exists", return_value=True):
                tracker = OfflineEmissionsTracker(
                    country_iso_code="FRA",
                    force_carbon_intensity_g_co2e_kwh=0,
                    save_to_file=False,
                    allow_multiple_runs=True,
                )

        self.assertEqual(tracker.force_carbon_intensity_g_co2e_kwh, 0.0)

    def test_force_carbon_intensity_rejects_negative_parameter(self):
        with patch("builtins.open", new_callable=get_custom_mock_open("", "")):
            with patch("os.path.exists", return_value=True):
                tracker = EmissionsTracker(
                    force_carbon_intensity_g_co2e_kwh=-1,
                    save_to_file=False,
                    allow_multiple_runs=True,
                )

        self.assertIsNone(tracker.force_carbon_intensity_g_co2e_kwh)
        self.assertIsNone(tracker._conf["force_carbon_intensity_g_co2e_kwh"])

    def test_force_carbon_intensity_rejects_non_numeric_parameter(self):
        with patch("builtins.open", new_callable=get_custom_mock_open("", "")):
            with patch("os.path.exists", return_value=True):
                tracker = EmissionsTracker(
                    force_carbon_intensity_g_co2e_kwh="invalid",
                    save_to_file=False,
                    allow_multiple_runs=True,
                )

        self.assertIsNone(tracker.force_carbon_intensity_g_co2e_kwh)
        self.assertIsNone(tracker._conf["force_carbon_intensity_g_co2e_kwh"])

    def test_track_emissions_forwards_force_carbon_intensity_parameter(self):
        with patch("codecarbon.emissions_tracker.EmissionsTracker") as tracker_class:

            @track_emissions(
                force_carbon_intensity_g_co2e_kwh=321.0,
                save_to_file=False,
            )
            def tracked_function():
                return "success"

            self.assertEqual(tracked_function(), "success")

        tracker_class.assert_called_once()
        self.assertEqual(
            tracker_class.call_args.kwargs["force_carbon_intensity_g_co2e_kwh"],
            321.0,
        )

    def test_track_emissions_forwards_force_carbon_intensity_to_offline_tracker(self):
        with patch(
            "codecarbon.emissions_tracker.OfflineEmissionsTracker"
        ) as tracker_class:

            @track_emissions(
                offline=True,
                country_iso_code="FRA",
                force_carbon_intensity_g_co2e_kwh=321.0,
                save_to_file=False,
            )
            def tracked_function():
                return "success"

            self.assertEqual(tracked_function(), "success")

        tracker_class.assert_called_once()
        self.assertEqual(
            tracker_class.call_args.kwargs["force_carbon_intensity_g_co2e_kwh"],
            321.0,
        )

    @mock.patch.dict(
        os.environ,
        {
            "CUDA_VISIBLE_DEVICES": "2, 3",
        },
    )
    def test_gpu_ids_from_env(self):
        with patch("os.path.exists", return_value=True):
            tracker = EmissionsTracker(
                project_name="test-project", allow_multiple_runs=True
            )
        self.assertEqual(tracker._gpu_ids, ["2", "3"])

    @mock.patch.dict(
        os.environ,
        {
            "CUDA_VISIBLE_DEVICES": "99",
        },
    )
    def test_too_much_gpu_ids_in_env(self):
        # GPU numbers start from 0, so 1 mean 2 GPUs
        with patch("os.path.exists", return_value=True):
            tracker = EmissionsTracker(
                project_name="test-project", allow_multiple_runs=True
            )
        self.assertEqual(tracker._gpu_ids, ["99"])
        gpu_count = 0
        for hardware in tracker._hardware:
            if isinstance(hardware, GPU):
                gpu_count += 1
        # self.assertEqual(gpu_count, 0)
        tracker.stop()

    @mock.patch.dict(
        os.environ,
        {
            "ROCR_VISIBLE_DEVICES": "1, 2",
        },
    )
    def test_gpu_ids_from_rocr_visible_devices(self):
        with patch("os.path.exists", return_value=True):
            tracker = EmissionsTracker(
                project_name="test-project", allow_multiple_runs=True
            )
        self.assertEqual(tracker._gpu_ids, ["1", "2"])

    @mock.patch.dict(
        os.environ,
        {
            "CUDA_VISIBLE_DEVICES": "0, 1",
            "ROCR_VISIBLE_DEVICES": "1, 2",
        },
    )
    def test_cuda_visible_devices_takes_precedence_over_rocr_visible_devices(self):
        # CUDA_VISIBLE_DEVICES should take precedence as NVIDIA GPUs are checked first
        with patch("os.path.exists", return_value=True):
            tracker = EmissionsTracker(
                project_name="test-project", allow_multiple_runs=True
            )
        self.assertEqual(tracker._gpu_ids, ["0", "1"])


if __name__ == "__main__":
    unittest.main()
