import builtins
import unittest
from pathlib import Path

from codecarbon.input import DataSource


# don't use vanilla unittest.mock.mock_openfor <3.7 compatibility
# https://stackoverflow.com/a/41656192/3867406
def mock_open(*args, **kargs):
    f_open = unittest.mock.mock_open(*args, **kargs)
    f_open.return_value.__iter__ = lambda self: iter(self.readline, "")
    return f_open


OPEN = builtins.open


def get_test_data_source() -> DataSource:
    return DataSource()


def get_custom_mock_open(global_conf_str, local_conf_str) -> callable:
    def mocked_open():
        def conditional_open_func(path, *args, **kwargs):
            p = Path(path).expanduser().resolve()
            if p.name == ".codecarbon.config":
                if p.parent == Path.home():
                    return mock_open(read_data=global_conf_str)()
                return mock_open(read_data=local_conf_str)()
            return OPEN(path, *args, **kwargs)

        return conditional_open_func

    return mocked_open
