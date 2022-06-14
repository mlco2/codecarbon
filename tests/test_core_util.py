import shutil
import tempfile

from codecarbon.core.util import backup, resolve_path


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
