import unittest
from unittest.mock import mock_open, patch

from codecarbon.lock import LOCKFILE, Lock


class TestLock(unittest.TestCase):
    def setUp(self):
        self.lock = Lock()

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_acquire_lock_creates_lock_file(self, mock_file, mock_remove):
        self.lock.acquire()
        mock_file.assert_called_once_with(LOCKFILE, "x")
        self.assertTrue(self.lock._has_created_lock)

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_acquire_lock_exits_when_lock_file_exists(self, mock_file, mock_remove):
        mock_file.side_effect = FileExistsError
        with self.assertRaises(FileExistsError):
            self.lock.acquire()

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_release_removes_lock_file(self, mock_file, mock_remove):
        self.lock.acquire()
        self.lock.release()
        mock_remove.assert_called_once_with(LOCKFILE)

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_release_does_not_release_when_not_created_by_this_instance(
        self, mock_file, mock_remove
    ):
        self.lock.release()
        mock_remove.assert_not_called()
        self.assertFalse(self.lock._has_created_lock)


if __name__ == "__main__":
    unittest.main()
