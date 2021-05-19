import os
import unittest
from textwrap import dedent
from unittest import mock
from unittest.mock import patch

from codecarbon.core.config import (
    clean_env_key,
    get_hierarchical_config,
    parse_env_config,
    parse_gpu_ids,
)
from codecarbon.emissions_tracker import EmissionsTracker
from tests.testutils import get_custom_mock_open


class TestConfig(unittest.TestCase):
    def test_clean_env_key(self):
        for key in [1, None, 0.2, [], set()]:
            with self.assertRaises(AssertionError):
                clean_env_key(key)
        for (key, target) in [
            ("", ""),
            ("USER", "user"),
            ("CODECARBON_TEST", "test"),
            ("CODECARBON_TEST_VALUE", "test_value"),
            ("CODECARBON_TEST_1", "test_1"),
            ("CODECARBON_1", "1"),
        ]:
            self.assertEqual(clean_env_key(key), target)

    def test_parse_gpu_ids(self):
        for (ids, target) in [
            ("0,1,2", [0, 1, 2]),
            ("[0, 1, 2", [0, 1, 2]),
            ("(0, 1, 2)", [0, 1, 2]),
            ("[1]", [1]),
            ("1", [1]),
            ("0", [0]),
            ("", []),
            (1, 1),
        ]:
            self.assertEqual(parse_gpu_ids(ids), target)

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
            {"codecarbon": {"test": "test-VALUE", "test_key": "this_other_value"}},
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
                "no_overwrite": "path/to/somewhere",
                "local_overwrite": "SUCCESS:overwritten",
                "syntax_test_key": "no/space= problem2",
                "local_new_key": "cool value",
            }
            self.assertDictEqual(conf, target)

    @mock.patch.dict(
        os.environ,
        {
            "USER": "useless key",
            "CODECARBON_ENV_OVERWRITE": "SUCCESS:overwritten",
            "CODECARBON_ENV_NEW_KEY": "cool value",
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
            target = {}
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
            output_dir=ERROR:not overwritten
            save_to_file=ERROR:not overwritten
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
            tracker = EmissionsTracker(
                project_name="test-project", co2_signal_api_token="signal-token"
            )
            self.assertEqual(tracker._measure_power_secs, 10)
            self.assertEqual(tracker._output_dir, "/success/overwritten")
            self.assertEqual(tracker._emissions_endpoint, "http://testhost:2000")
            self.assertEqual(tracker._gpu_ids, [0, 1])
            self.assertEqual(tracker._co2_signal_api_token, "signal-token")
            self.assertEqual(tracker._project_name, "test-project")
            self.assertTrue(tracker._save_to_file)
