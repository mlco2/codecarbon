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
def test_multiple_rapl_providers_with_mixed_permissions(tmp_path):
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
        os.chmod(energy_mmio, 0)

        # is_rapl_available should return True because intel-rapl:0 is readable
        assert is_rapl_available(rapl_dir=str(base))

        # Creating IntelRAPL should succeed and use the readable domain
        rapl = IntelRAPL(rapl_dir=str(base))

        # Should have found the readable intel-rapl:0 domain
        assert len(rapl._rapl_files) == 1
        assert "intel-rapl/intel-rapl:0/energy_uj" in rapl._rapl_files[0].path

        # A warning should be emitted for the unreadable MMIO domain
        messages = [r.getMessage() for r in log_records]
        assert any(
            "Permission denied reading RAPL file" in m and "intel-rapl-mmio" in m
            for m in messages
        ), f"Expected permission warning for intel-rapl-mmio, got: {messages}"

    finally:
        codecarbon_logger.removeHandler(test_handler)
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


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_deduplication_prefers_mmio(tmp_path):
    """
    Verify that when the same domain (e.g., package-0) appears in both
    intel-rapl and intel-rapl-mmio, only the MMIO version is used to
    prevent double-counting. Subdomains (core, uncore) are filtered out
    when package domains exist to avoid double-counting.
    """
    base = tmp_path

    # Create intel-rapl provider with package-0 domain
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    d0_msr = rapl_provider / "intel-rapl:0"
    d0_msr.mkdir()
    (d0_msr / "name").write_text("package-0")
    (d0_msr / "energy_uj").write_text("52649883221")
    (d0_msr / "max_energy_range_uj").write_text("262143328850")

    # Create intel-rapl-mmio provider with the same package-0 domain
    mmio_provider = base / "intel-rapl-mmio"
    mmio_provider.mkdir()

    d0_mmio = mmio_provider / "intel-rapl-mmio:0"
    d0_mmio.mkdir()
    (d0_mmio / "name").write_text("package-0")
    (d0_mmio / "energy_uj").write_text("99999999999")
    (d0_mmio / "max_energy_range_uj").write_text("262143328850")

    # Create a unique domain in MSR (core)
    d0_core = rapl_provider / "intel-rapl:0:0"
    d0_core.mkdir()
    (d0_core / "name").write_text("core")
    (d0_core / "energy_uj").write_text("11111111111")
    (d0_core / "max_energy_range_uj").write_text("262143328850")

    # is_rapl_available should return True
    assert is_rapl_available(rapl_dir=str(base))

    # Create IntelRAPL instance
    rapl = IntelRAPL(rapl_dir=str(base))

    # Should have exactly 1 RAPL file: package-0 (MMIO)
    # Core domain is filtered out to avoid double-counting since it's a subdomain of package
    assert len(rapl._rapl_files) == 1, f"Expected 1 file, got {len(rapl._rapl_files)}"

    # Verify package-0 is from MMIO (newer interface)
    package_files = [f for f in rapl._rapl_files if "Processor Energy" in f.name]
    assert (
        len(package_files) == 1
    ), "Should have exactly one package domain after deduplication"

    # The package file should be from intel-rapl-mmio
    assert (
        "intel-rapl-mmio" in package_files[0].path
    ), f"Expected MMIO path, got: {package_files[0].path}"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_psys_not_preferred_when_package_available(tmp_path):
    """
    Verify that when both psys and package domains are available, CodeCarbon prefers
    package domains over psys because package domains are more reliable and update
    correctly under load, while psys may not on some Intel systems.
    """
    base = tmp_path

    # Create intel-rapl provider
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create psys domain (platform power - most comprehensive)
    d_psys = rapl_provider / "intel-rapl:1"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create package-0 domain (subset of psys)
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create core domain (subset of package and psys)
    d_core = rapl_provider / "intel-rapl:0:0"
    d_core.mkdir()
    (d_core / "name").write_text("core")
    (d_core / "energy_uj").write_text("11111111111")
    (d_core / "max_energy_range_uj").write_text("262143328850")

    # Create uncore domain (subset of package and psys)
    d_uncore = rapl_provider / "intel-rapl:0:1"
    d_uncore.mkdir()
    (d_uncore / "name").write_text("uncore")
    (d_uncore / "energy_uj").write_text("22222222222")
    (d_uncore / "max_energy_range_uj").write_text("262143328850")

    # is_rapl_available should return True
    assert is_rapl_available(rapl_dir=str(base))

    # Create IntelRAPL instance
    rapl = IntelRAPL(rapl_dir=str(base))

    # Should have 1 RAPL file: package-0 (not psys)
    # Package domains are preferred over psys for reliability
    assert (
        len(rapl._rapl_files) == 1
    ), f"Expected 1 file (package), got {len(rapl._rapl_files)}"

    # Verify it's the package domain (not psys)
    assert (
        "Processor Energy" in rapl._rapl_files[0].name
        and "intel-rapl:0" in rapl._rapl_files[0].path
    ), f"Expected package-0 domain, got: {rapl._rapl_files[0].name} at {rapl._rapl_files[0].path}"

    # Verify psys is NOT used (should be logged as detected but not used)
    assert (
        "intel-rapl:1" not in rapl._rapl_files[0].path
    ), "psys should not be used when package domains are available"
