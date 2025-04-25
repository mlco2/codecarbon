import os
import tempfile

from codecarbon.core.util import backup, resolve_path


def test_backup():
    first_file = tempfile.NamedTemporaryFile(delete=False)
    first_file_path = first_file.name
    first_file.close()

    backup(first_file_path)
    expected_backup_path = resolve_path(f"{first_file_path}.bak")
    assert expected_backup_path.exists()

    with open(first_file_path, "w") as f:
        f.write("new content")

    backup(first_file_path)
    backup_of_backup_path = resolve_path(f"{first_file_path}_0.bak")
    assert backup_of_backup_path.exists()

    if os.path.exists(expected_backup_path):
        os.unlink(expected_backup_path)
    if os.path.exists(backup_of_backup_path):
        os.unlink(backup_of_backup_path)
