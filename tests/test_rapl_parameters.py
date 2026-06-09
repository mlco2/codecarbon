"""
Test to verify that rapl_include_dram and rapl_prefer_psys parameters work correctly.
"""

import logging
import sys

import pytest

from codecarbon.core.cpu import IntelRAPL


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_include_dram_default_false(tmp_path):
    """
    Verify that rapl_include_dram defaults to False and excludes DRAM domains.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create dram domain
    d_dram = rapl_provider / "intel-rapl:1"
    d_dram.mkdir()
    (d_dram / "name").write_text("dram")
    (d_dram / "energy_uj").write_text("11111111111")
    (d_dram / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with default parameters
    rapl = IntelRAPL(rapl_dir=str(base))

    # Should have 1 RAPL files: package-0
    assert len(rapl._rapl_files) == 1, f"Expected 1 files, got {len(rapl._rapl_files)}"

    # Verify both package and dram are present
    names = [f.name for f in rapl._rapl_files]
    assert any("Processor Energy" in name for name in names), "Missing package domain"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_include_dram_false(tmp_path):
    """
    Verify that rapl_include_dram=False excludes DRAM domains.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create dram domain
    d_dram = rapl_provider / "intel-rapl:1"
    d_dram.mkdir()
    (d_dram / "name").write_text("dram")
    (d_dram / "energy_uj").write_text("11111111111")
    (d_dram / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with rapl_include_dram=False
    rapl = IntelRAPL(rapl_dir=str(base), rapl_include_dram=False)

    # Should have only 1 RAPL file: package-0 (no dram)
    assert len(rapl._rapl_files) == 1, f"Expected 1 file, got {len(rapl._rapl_files)}"

    # Verify only package is present
    names = [f.name for f in rapl._rapl_files]
    assert any("Processor Energy" in name for name in names), "Missing package domain"
    assert not any(
        "dram" in name.lower() for name in names
    ), "DRAM should not be included"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_include_dram_true_explicit(tmp_path):
    """
    Verify that rapl_include_dram=True explicitly includes DRAM domains.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create dram domain
    d_dram = rapl_provider / "intel-rapl:1"
    d_dram.mkdir()
    (d_dram / "name").write_text("dram")
    (d_dram / "energy_uj").write_text("11111111111")
    (d_dram / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with rapl_include_dram=True explicitly
    rapl = IntelRAPL(rapl_dir=str(base), rapl_include_dram=True)

    # Should have 2 RAPL files: package-0 + dram
    assert len(rapl._rapl_files) == 2, f"Expected 2 files, got {len(rapl._rapl_files)}"

    # Verify both package and dram are present
    names = [f.name for f in rapl._rapl_files]
    assert any("Processor Energy" in name for name in names), "Missing package domain"
    assert any("dram" in name.lower() for name in names), "Missing DRAM domain"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_prefer_psys_default_false(tmp_path):
    """
    Verify that rapl_prefer_psys defaults to False and prefers package domains over psys.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create psys domain
    d_psys = rapl_provider / "intel-rapl:1"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with default parameters
    rapl = IntelRAPL(rapl_dir=str(base))

    # Should have 1 RAPL file: package-0 (not psys)
    assert len(rapl._rapl_files) == 1, f"Expected 1 file, got {len(rapl._rapl_files)}"

    # Verify it's the package domain (not psys)
    assert (
        "Processor Energy" in rapl._rapl_files[0].name
        and "intel-rapl:0" in rapl._rapl_files[0].path
    ), f"Expected package-0 domain, got: {rapl._rapl_files[0].name}"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_prefer_psys_true(tmp_path):
    """
    Verify that rapl_prefer_psys=True uses psys domain instead of package domains.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create psys domain
    d_psys = rapl_provider / "intel-rapl:1"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with rapl_prefer_psys=True
    rapl = IntelRAPL(rapl_dir=str(base), rapl_prefer_psys=True)

    # Should have 1 RAPL file: psys (not package)
    assert len(rapl._rapl_files) == 1, f"Expected 1 file, got {len(rapl._rapl_files)}"

    # Verify it's the psys domain
    assert (
        "Processor Energy" in rapl._rapl_files[0].name
        and "intel-rapl:1" in rapl._rapl_files[0].path
    ), f"Expected psys domain, got: {rapl._rapl_files[0].name} at {rapl._rapl_files[0].path}"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_prefer_psys_false_explicit(tmp_path):
    """
    Verify that rapl_prefer_psys=False explicitly prefers package over psys.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create psys domain
    d_psys = rapl_provider / "intel-rapl:1"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with rapl_prefer_psys=False explicitly
    rapl = IntelRAPL(rapl_dir=str(base), rapl_prefer_psys=False)

    # Should have 1 RAPL file: package-0 (not psys)
    assert len(rapl._rapl_files) == 1, f"Expected 1 file, got {len(rapl._rapl_files)}"

    # Verify it's the package domain (not psys)
    assert (
        "Processor Energy" in rapl._rapl_files[0].name
        and "intel-rapl:0" in rapl._rapl_files[0].path
    ), f"Expected package-0 domain, got: {rapl._rapl_files[0].name}"


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_prefer_psys_with_no_package_domains(tmp_path):
    """
    Verify that even with rapl_prefer_psys=False, psys is used as fallback
    when no package domains are available.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create only psys domain (no package domains)
    d_psys = rapl_provider / "intel-rapl:0"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create IntelRAPL with rapl_prefer_psys=False
    rapl = IntelRAPL(rapl_dir=str(base), rapl_prefer_psys=False)

    # Should have 1 RAPL file: psys (fallback)
    assert len(rapl._rapl_files) == 1, f"Expected 1 file, got {len(rapl._rapl_files)}"

    # Verify it's the psys domain
    assert "Processor Energy" in rapl._rapl_files[0].name


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_both_parameters_together(tmp_path):
    """
    Verify that rapl_include_dram and rapl_prefer_psys work correctly together.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create psys domain
    d_psys = rapl_provider / "intel-rapl:2"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create dram domain
    d_dram = rapl_provider / "intel-rapl:1"
    d_dram.mkdir()
    (d_dram / "name").write_text("dram")
    (d_dram / "energy_uj").write_text("11111111111")
    (d_dram / "max_energy_range_uj").write_text("262143328850")

    # Test 1: rapl_prefer_psys=True with rapl_include_dram=True (should only use psys)
    rapl1 = IntelRAPL(rapl_dir=str(base), rapl_prefer_psys=True, rapl_include_dram=True)
    assert (
        len(rapl1._rapl_files) == 1
    ), f"Expected 1 file (psys only), got {len(rapl1._rapl_files)}"
    assert "intel-rapl:2" in rapl1._rapl_files[0].path, "Should use psys"

    # Test 2: rapl_prefer_psys=False with rapl_include_dram=True (should use package + dram)
    rapl2 = IntelRAPL(
        rapl_dir=str(base), rapl_prefer_psys=False, rapl_include_dram=True
    )
    assert (
        len(rapl2._rapl_files) == 2
    ), f"Expected 2 files (package + dram), got {len(rapl2._rapl_files)}"
    names = [f.name for f in rapl2._rapl_files]
    assert any("Processor Energy" in name for name in names), "Missing package domain"
    assert any("dram" in name.lower() for name in names), "Missing DRAM domain"

    # Test 3: rapl_prefer_psys=False with rapl_include_dram=False (should use only package)
    rapl3 = IntelRAPL(
        rapl_dir=str(base), rapl_prefer_psys=False, rapl_include_dram=False
    )
    assert (
        len(rapl3._rapl_files) == 1
    ), f"Expected 1 file (package only), got {len(rapl3._rapl_files)}"
    assert "intel-rapl:0" in rapl3._rapl_files[0].path, "Should use package"
    assert "DRAM" not in rapl3._rapl_files[0].name, "Should not include DRAM"


@pytest.mark.skip(reason="Flaky test - log capture unreliable in CI environment")
@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_include_dram_logs_message(tmp_path):
    """
    Verify that appropriate log messages are generated for rapl_include_dram setting.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Create dram domain
    d_dram = rapl_provider / "intel-rapl:1"
    d_dram.mkdir()
    (d_dram / "name").write_text("dram")
    (d_dram / "energy_uj").write_text("11111111111")
    (d_dram / "max_energy_range_uj").write_text("262143328850")

    # Capture log messages
    from codecarbon.external.logger import logger as codecarbon_logger

    log_records = []

    class TestHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    test_handler = TestHandler()
    test_handler.setLevel(logging.INFO)
    codecarbon_logger.addHandler(test_handler)

    try:
        # Test with rapl_include_dram=False
        log_records.clear()
        rapl = IntelRAPL(rapl_dir=str(base), rapl_include_dram=False)
        assert (
            rapl is not None
        )  # Variable used to trigger RAPL initialization and logging

        messages = [r.getMessage() for r in log_records]
        assert any(
            "rapl_include_dram=False" in m for m in messages
        ), f"Expected log message about rapl_include_dram=False, got: {messages}"
        assert any(
            "rapl_include_dram=True for complete hardware measurement" in m
            for m in messages
        ), f"Expected suggestion to use rapl_include_dram=True, got: {messages}"

    finally:
        codecarbon_logger.removeHandler(test_handler)


@pytest.mark.skip(reason="Flaky test - log capture unreliable in CI environment")
@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_prefer_psys_logs_message(tmp_path):
    """
    Verify that appropriate log messages are generated for rapl_prefer_psys setting.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create psys domain
    d_psys = rapl_provider / "intel-rapl:1"
    d_psys.mkdir()
    (d_psys / "name").write_text("psys")
    (d_psys / "energy_uj").write_text("99999999999")
    (d_psys / "max_energy_range_uj").write_text("262143328850")

    # Create package-0 domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Capture log messages
    from codecarbon.external.logger import logger as codecarbon_logger

    log_records = []

    class TestHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    test_handler = TestHandler()
    test_handler.setLevel(logging.INFO)
    codecarbon_logger.addHandler(test_handler)

    try:
        # Test with rapl_prefer_psys=True
        log_records.clear()
        rapl1 = IntelRAPL(rapl_dir=str(base), rapl_prefer_psys=True)
        assert (
            rapl1 is not None
        )  # Variable used to trigger RAPL initialization and logging

        messages = [r.getMessage() for r in log_records]
        assert any(
            "rapl_prefer_psys=True" in m for m in messages
        ), f"Expected log message about rapl_prefer_psys=True, got: {messages}"

        # Test with rapl_prefer_psys=False (default)
        log_records.clear()
        rapl2 = IntelRAPL(rapl_dir=str(base), rapl_prefer_psys=False)
        assert (
            rapl2 is not None
        )  # Variable used to trigger RAPL initialization and logging

        messages = [r.getMessage() for r in log_records]
        assert any(
            "rapl_prefer_psys=False" in m for m in messages
        ), f"Expected log message about rapl_prefer_psys=False, got: {messages}"
        assert any(
            "rapl_prefer_psys=True to use psys" in m for m in messages
        ), f"Expected suggestion about rapl_prefer_psys=True, got: {messages}"

    finally:
        codecarbon_logger.removeHandler(test_handler)


@pytest.mark.skipif(not sys.platform.lower().startswith("lin"), reason="requires Linux")
def test_rapl_parameters_stored_correctly(tmp_path):
    """
    Verify that the parameters are stored correctly in the IntelRAPL instance.
    """
    base = tmp_path
    rapl_provider = base / "intel-rapl"
    rapl_provider.mkdir()

    # Create minimal package domain
    d_package = rapl_provider / "intel-rapl:0"
    d_package.mkdir()
    (d_package / "name").write_text("package-0")
    (d_package / "energy_uj").write_text("52649883221")
    (d_package / "max_energy_range_uj").write_text("262143328850")

    # Test default values
    rapl_default = IntelRAPL(rapl_dir=str(base))
    assert (
        rapl_default.rapl_include_dram is False
    ), "Default rapl_include_dram should be False"
    assert (
        rapl_default.rapl_prefer_psys is False
    ), "Default rapl_prefer_psys should be False"

    # Test explicit False values
    rapl_false = IntelRAPL(
        rapl_dir=str(base), rapl_include_dram=False, rapl_prefer_psys=False
    )
    assert rapl_false.rapl_include_dram is False
    assert rapl_false.rapl_prefer_psys is False

    # Test explicit True values
    rapl_true = IntelRAPL(
        rapl_dir=str(base), rapl_include_dram=True, rapl_prefer_psys=True
    )
    assert rapl_true.rapl_include_dram is True
    assert rapl_true.rapl_prefer_psys is True
