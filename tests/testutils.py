import builtins
from pathlib import Path
from unittest.mock import mock_open

from codecarbon.input import DataSource

OPEN = builtins.open


def get_test_data_source() -> DataSource:
    return DataSource()


def get_custom_mock_open(global_conf_str, local_conf_str) -> callable:
    def mocked_open():
        def conditional_open_func(path, *args, **kwargs):
            p = Path(path).expanduser().resolve()
            if p.name == ".codecarbon.config":
                if p.parent == Path.home():
                    print(f"\nAsking for {path} returning GLOBAL\n")
                    return mock_open(read_data=global_conf_str)()
                print(f"\nAsking for {path} returning LOCAL\n")
                return mock_open(read_data=local_conf_str)()
            print(f"\nAsking for {path} returning OPEN\n")
            return OPEN(path, *args, **kwargs)

        return conditional_open_func

    return mocked_open
