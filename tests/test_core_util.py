import shutil
import tempfile

from codecarbon.core.util import backup, detect_cpu_model, resolve_path


def test_detect_cpu_model_caching():
    """Test that detect_cpu_model() results are cached."""
    # Clear cache to ensure clean state
    detect_cpu_model.cache_clear()

    # First call should populate cache
    result1 = detect_cpu_model()
    cache_info1 = detect_cpu_model.cache_info()
    assert cache_info1.hits == 0
    assert cache_info1.misses == 1

    # Second call should hit cache
    result2 = detect_cpu_model()
    cache_info2 = detect_cpu_model.cache_info()
    assert cache_info2.hits == 1
    assert cache_info2.misses == 1

    # Results should be identical
    assert result1 == result2

    # Third call should also hit cache
    detect_cpu_model()
    cache_info3 = detect_cpu_model.cache_info()
    assert cache_info3.hits == 2
    assert cache_info3.misses == 1


def test_backup():
    first_file = tempfile.NamedTemporaryFile()
    backup(first_file.name)
    expected_backup_path = resolve_path(f"{first_file.name}.bak")
    assert expected_backup_path.exists()
    # re-create file and back it up again
    second_file = tempfile.NamedTemporaryFile()
    shutil.copyfile(second_file.name, first_file.name)
    backup(first_file.name)
    backup_of_backup_path = resolve_path(f"{first_file.name}_0.bak")
    assert backup_of_backup_path.exists()
