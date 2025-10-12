"""
Test to verify that intel-rapl-mmio and other providers are properly scanned
and permission errors are gracefully handled.
"""

import logging
import os
import stat
import sys

import pytest

from codecarbon.core.cpu import IntelRAPL, is_rapl_available


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_multiple_rapl_providers_with_mixed_permissions(tmp_path, caplog):
    """
    Verify that multiple RAPL providers (intel-rapl and intel-rapl-mmio) are
    scanned, and permission errors on one provider don't prevent using the other.
    """
    base = tmp_path

    # Create intel-rapl provider with readable package domain
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    d0 = rapl_provider / "intel-rapl:0"
    d0.mkdir()
    (d0 / "name").write_text("package-0")
    (d0 / "energy_uj").write_text("52649883221")
    (d0 / "max_energy_range_uj").write_text("262143328850")

    # Create intel-rapl-mmio provider with unreadable domain
    mmio_provider = base / "intel-rapl-mmio"
    mmio_provider.mkdir()

    d_mmio = mmio_provider / "intel-rapl-mmio:0"
    d_mmio.mkdir()
    (d_mmio / "name").write_text("package-0")
    energy_mmio = d_mmio / "energy_uj"
    energy_mmio.write_text("99999999999")
    (d_mmio / "max_energy_range_uj").write_text("262143328850")

    # Make the MMIO energy file unreadable
    mode_before = energy_mmio.stat().st_mode
    caplog.set_level(logging.WARNING, logger="codecarbon")

    try:
        os.chmod(energy_mmio, 0)

        # is_rapl_available should return True because intel-rapl:0 is readable
        assert is_rapl_available(rapl_dir=str(base))

        # Creating IntelRAPL should succeed and use the readable domain
        rapl = IntelRAPL(rapl_dir=str(base))

        # Should have found the readable intel-rapl:0 domain
        assert len(rapl._rapl_files) == 1
        assert "intel-rapl/intel-rapl:0/energy_uj" in rapl._rapl_files[0].path

        # A warning should be emitted for the unreadable MMIO domain
        messages = [r.getMessage() for r in caplog.records]
        assert any(
            "Permission denied reading RAPL file" in m and "intel-rapl-mmio" in m
            for m in messages
        ), f"Expected permission warning for intel-rapl-mmio, got: {messages}"

    finally:
        try:
            os.chmod(energy_mmio, stat.S_IMODE(mode_before) or 0o644)
        except Exception:
            pass


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_all_providers_unreadable_returns_false(tmp_path):
    """
    Verify that is_rapl_available returns False when all main/package domains
    are unreadable across all providers.
    """
    base = tmp_path

    # Create intel-rapl provider with unreadable package domain
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    d0 = rapl_provider / "intel-rapl:0"
    d0.mkdir()
    (d0 / "name").write_text("package-0")
    energy0 = d0 / "energy_uj"
    energy0.write_text("52649883221")
    (d0 / "max_energy_range_uj").write_text("262143328850")

    # Create intel-rapl-mmio provider with unreadable domain
    mmio_provider = base / "intel-rapl-mmio"
    mmio_provider.mkdir()

    d_mmio = mmio_provider / "intel-rapl-mmio:0"
    d_mmio.mkdir()
    (d_mmio / "name").write_text("package-0")
    energy_mmio = d_mmio / "energy_uj"
    energy_mmio.write_text("99999999999")
    (d_mmio / "max_energy_range_uj").write_text("262143328850")

    # Make both energy files unreadable
    mode_before_0 = energy0.stat().st_mode
    mode_before_mmio = energy_mmio.stat().st_mode

    try:
        os.chmod(energy0, 0)
        os.chmod(energy_mmio, 0)

        # is_rapl_available should return False because no main domain is readable
        assert not is_rapl_available(rapl_dir=str(base))

        # Creating IntelRAPL should succeed but have no RAPL files
        rapl = IntelRAPL(rapl_dir=str(base))
        assert len(rapl._rapl_files) == 0

    finally:
        try:
            os.chmod(energy0, stat.S_IMODE(mode_before_0) or 0o644)
            os.chmod(energy_mmio, stat.S_IMODE(mode_before_mmio) or 0o644)
        except Exception:
            pass
