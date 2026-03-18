from unittest.mock import MagicMock, patch

import pytest

from codecarbon.core.resource_tracker import ResourceTracker


@pytest.mark.parametrize(
    "is_mac, is_windows, is_linux, cpu_model, expected_fragment",
    [
        # Mac + ARM chip
        (True, False, False, "Apple M4", "PowerMetrics sudo"),
        # Mac + Intel chip
        (True, False, False, "Intel Core i7", "Intel Power Gadget"),
        # Mac + cpu_model is None
        (True, False, False, None, "Intel Power Gadget"),
        # Windows
        (False, True, False, "Intel Core i7", "Intel Power Gadget"),
        # Linux
        (False, False, True, "Intel Core i7", "RAPL"),
        # Unknown OS
        (False, False, False, "Intel Core i7", ""),
    ],
)
def test_get_install_instructions(
    is_mac, is_windows, is_linux, cpu_model, expected_fragment
):
    tracker = MagicMock()
    resource_tracker = ResourceTracker(tracker)

    with (
        patch("codecarbon.core.resource_tracker.is_mac_os", return_value=is_mac),
        patch(
            "codecarbon.core.resource_tracker.is_windows_os", return_value=is_windows
        ),
        patch("codecarbon.core.resource_tracker.is_linux_os", return_value=is_linux),
        patch(
            "codecarbon.core.resource_tracker.detect_cpu_model", return_value=cpu_model
        ),
    ):
        result = resource_tracker._get_install_instructions()

    assert expected_fragment in result
