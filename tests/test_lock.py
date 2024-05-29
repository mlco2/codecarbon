import unittest
from unittest.mock import mock_open, patch

import codecarbon.lock as lock


class TestLock(unittest.TestCase):
    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_acquire_lock_creates_lock_file(self, mock_file, mock_remove):
        lock.lock_file_created_by_this_process = False
        lock.acquire_lock()
        mock_file.assert_called_once_with(lock.LOCKFILE, "x")
        self.assertTrue(lock.lock_file_created_by_this_process)

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_acquire_lock_exits_when_lock_file_exists(self, mock_file, mock_remove):
        mock_file.side_effect = FileExistsError
        with self.assertRaises(SystemExit):
            lock.acquire_lock()

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_remove_lock_file_removes_lock_file(self, mock_file, mock_remove):
        lock.lock_file_created_by_this_process = True
        lock._remove_lock_file()
        mock_remove.assert_called_once_with(lock.LOCKFILE)

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_remove_lock_file_does_not_remove_lock_file_when_not_created_by_this_process(
        self, mock_file, mock_remove
    ):
        lock.lock_file_created_by_this_process = False
        lock._remove_lock_file()
        mock_remove.assert_not_called()


if __name__ == "__main__":
    unittest.main()
