import builtins
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

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


@contextmanager
def ensure_telemetry_run_duration(min_seconds: float = 10.0):
    """Force tracker stop emissions duration above telemetry's 1s minimum."""
    from codecarbon.emissions_tracker import BaseEmissionsTracker

    original_prepare = BaseEmissionsTracker._prepare_emissions_data

    def prepare_with_min_duration(self):
        data = original_prepare(self)
        if data is not None and (data.duration is None or data.duration < min_seconds):
            data.duration = min_seconds
        return data

    with patch.object(
        BaseEmissionsTracker, "_prepare_emissions_data", prepare_with_min_duration
    ):
        yield
