import logging
import os
import stat
import sys

import pytest

from codecarbon.core.cpu import IntelRAPL, is_rapl_available


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_main_rapl_permission_error(tmp_path):
    """If the main/package energy file is not readable we must fail loudly."""
    base = tmp_path
    # Create proper RAPL hierarchy: base/intel-rapl/intel-rapl:N/
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    d0 = rapl_provider / "intel-rapl:0"
    d0.mkdir()
    (d0 / "name").write_text("package-0")
    energy0 = d0 / "energy_uj"
    energy0.write_text("52649883221")
    (d0 / "max_energy_range_uj").write_text("262143328850")

    # another domain (readable)
    d1 = rapl_provider / "intel-rapl:1"
    d1.mkdir()
    (d1 / "name").write_text("psys")
    (d1 / "energy_uj").write_text("117870082040")
    (d1 / "max_energy_range_uj").write_text("262143328850")

    # Make the main energy file unreadable to simulate permission error
    mode_before = energy0.stat().st_mode
    try:
        os.chmod(energy0, 0)
        # The lightweight availability check should return False when the
        # main/package counter is unreadable.
        assert not is_rapl_available(rapl_dir=str(base))

        # Creating the IntelRAPL instance should *not* raise; it should
        # skip unreadable domains and continue.
        rapl = IntelRAPL(rapl_dir=str(base))
        # The unreadable main domain should be skipped; only the readable
        # non-main domain should be present.
        assert len(rapl._rapl_files) == 1
        assert rapl._rapl_files[0].path.endswith("intel-rapl/intel-rapl:1/energy_uj")
    finally:
        # restore permissions so tmp_path can be cleaned up
        try:
            os.chmod(energy0, stat.S_IMODE(mode_before) or 0o644)
        except Exception:
            pass


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_non_main_rapl_permission_warning_and_skip(tmp_path):
    """If a non-main domain (e.g. psys) is unreadable, it should be skipped and warn."""
    base = tmp_path
    # Create proper RAPL hierarchy: base/intel-rapl/intel-rapl:N/
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    d0 = rapl_provider / "intel-rapl:0"
    d0.mkdir()
    (d0 / "name").write_text("package-0")
    (d0 / "energy_uj").write_text("52649883221")
    (d0 / "max_energy_range_uj").write_text("262143328850")

    d1 = rapl_provider / "intel-rapl:1"
    d1.mkdir()
    (d1 / "name").write_text("psys")
    energy1 = d1 / "energy_uj"
    energy1.write_text("117870082040")
    (d1 / "max_energy_range_uj").write_text("262143328850")

    # Make the non-main energy file unreadable
    mode_before = energy1.stat().st_mode

    # Add a custom handler to capture warnings (since logger.propagate = False)
    from codecarbon.external.logger import logger as codecarbon_logger

    log_records = []

    class TestHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    test_handler = TestHandler()
    test_handler.setLevel(logging.WARNING)
    codecarbon_logger.addHandler(test_handler)

    try:
        os.chmod(energy1, 0)
        rapl = IntelRAPL(rapl_dir=str(base))
        # The unreadable non-main domain should be skipped
        assert len(rapl._rapl_files) == 1
        assert rapl._rapl_files[0].path.endswith("intel-rapl/intel-rapl:0/energy_uj")

        # A warning about permission denied should be emitted
        messages = [r.getMessage() for r in log_records]
        assert any(
            "Permission denied reading RAPL file" in m
            or "Permission denied listing" in m
            for m in messages
        ), f"Expected permission warning, got: {messages}"
    finally:
        codecarbon_logger.removeHandler(test_handler)
        try:
            os.chmod(energy1, stat.S_IMODE(mode_before) or 0o644)
        except Exception:
            pass
