import unittest
from unittest import mock
from unittest.mock import patch, mock_open
from textwrap import dedent
import os
from codecarbon.core.config import (
    clean_env_key,
    parse_env_config,
    get_hierarchical_config,
)
from pathlib import Path


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

    def custom_mock_open(self, *args, **kwargs):
        global_config_data = dedent(
            """\
            [codecarbon]
            cool_key=2
            test=path/to/test
            this_is_a_key= no/space= problem
            """
        )
        local_config_data = dedent(
            """\
            [codecarbon]
            cool_key=4
            new_key=cool
            """
        )

        def f(path, encoding=None):
            if Path(path).parent == Path(__file__).parent:
                return mock_open(read_data=local_config_data)()
            return mock_open(read_data=global_config_data)()

        return f

    def test_read_confs(self):

        with patch("builtins.open", new_callable=self.custom_mock_open) as mock_file:
            conf = dict(get_hierarchical_config())
            target = {
                "cool_key": "4",
                "test": "path/to/test",
                "this_is_a_key": "no/space= problem",
                "new_key": "cool",
            }
            self.assertDictEqual(conf, target)
