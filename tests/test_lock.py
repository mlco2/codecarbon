import atexit
import os
import signal
import threading
import unittest
from unittest.mock import mock_open, patch

from codecarbon.lock import LOCKFILE, Lock


class SignalSafeTestCase(unittest.TestCase):
    """acquire() installs process-wide handlers: put the originals back."""

    def setUp(self):
        self.original_handlers = {
            sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)
        }

    def tearDown(self):
        for sig, handler in self.original_handlers.items():
            signal.signal(sig, handler)


class TestLock(SignalSafeTestCase):
    def setUp(self):
        super().setUp()
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
    def test_release_is_idempotent(self, mock_file, mock_remove):
        # A second release() must not delete the lock file again: by then it may
        # have been re-created by another instance of codecarbon.
        self.lock.acquire()
        self.lock.release()
        self.lock.release()
        mock_remove.assert_called_once_with(LOCKFILE)
        self.assertFalse(self.lock._has_created_lock)

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_release_does_not_release_when_not_created_by_this_instance(
        self, mock_file, mock_remove
    ):
        self.lock.release()
        mock_remove.assert_not_called()
        self.assertFalse(self.lock._has_created_lock)

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_acquire_release_with_multiple_threads(self, mock_file, mock_remove):
        """
        Test that the lock file is created and removed correctly when multiple threads are used.
        """
        # Simulate a complex threading scenario where the lock file is created and removed multiple times
        # First call succeeds, second fails, third succeeds, subsequent calls raise FileExistsError
        mock_file.side_effect = (
            [mock_open().return_value]
            + [FileExistsError]
            + [mock_open().return_value]
            + [FileExistsError] * 7
        )

        def thread_target():
            # Create a lock instance in each thread
            lock = Lock()
            try:
                lock.acquire()
            except Exception:
                pass
            finally:
                lock.release()

        threads = [threading.Thread(target=thread_target, args=()) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Ensure that the lock file was created and removed correctly
        self.assertTrue(mock_file.called)
        self.assertTrue(mock_remove.called)


class TestLockSignalHandlers(SignalSafeTestCase):
    """The lock must not permanently steal the host application's handlers."""

    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_release_restores_previous_handlers(self, mock_file, mock_remove):
        def sentinel(signum, frame):
            pass

        signal.signal(signal.SIGTERM, sentinel)
        lock = Lock()
        lock.acquire()
        self.assertEqual(signal.getsignal(signal.SIGTERM), lock._handle_exit)
        lock.release()
        self.assertIs(signal.getsignal(signal.SIGTERM), sentinel)
        self.assertIs(
            signal.getsignal(signal.SIGINT), self.original_handlers[signal.SIGINT]
        )

    @unittest.skipIf(
        not hasattr(signal, "raise_signal"), "requires signal.raise_signal (3.8+)"
    )
    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_signal_is_forwarded_to_previous_handler(self, mock_file, mock_remove):
        received = []

        signal.signal(signal.SIGTERM, lambda signum, frame: received.append(signum))
        lock = Lock()
        lock.acquire()
        signal.raise_signal(signal.SIGTERM)
        self.assertEqual(received, [signal.SIGTERM])
        self.assertFalse(lock._previous_handlers)

    @unittest.skipIf(
        not hasattr(signal, "raise_signal"), "requires signal.raise_signal (3.8+)"
    )
    @patch("codecarbon.lock.os.kill")
    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_default_disposition_is_reproduced(self, mock_file, mock_remove, mock_kill):
        # No handler installed by the host application: the default disposition
        # of SIGTERM is to terminate, which the lock must reproduce after having
        # released the lock instead of silently swallowing the signal.
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        lock = Lock()
        lock.acquire()

        signal.raise_signal(signal.SIGTERM)

        mock_kill.assert_called_once_with(os.getpid(), signal.SIGTERM)
        # The lock was released before re-raising, and the default disposition
        # was put back so the re-raised signal is not caught again.
        self.assertTrue(mock_remove.called)
        self.assertIs(signal.getsignal(signal.SIGTERM), signal.SIG_DFL)

    @unittest.skipIf(
        not hasattr(signal, "raise_signal"), "requires signal.raise_signal (3.8+)"
    )
    @patch("codecarbon.lock.os.kill")
    @patch("codecarbon.lock.os.remove")
    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_ignored_signal_stays_ignored(self, mock_file, mock_remove, mock_kill):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        lock = Lock()
        lock.acquire()

        signal.raise_signal(signal.SIGTERM)

        # The host application asked to ignore SIGTERM: release the lock, but do
        # not terminate on its behalf.
        self.assertTrue(mock_remove.called)
        mock_kill.assert_not_called()
        self.assertIs(signal.getsignal(signal.SIGTERM), signal.SIG_IGN)

    @patch("codecarbon.lock.os.remove")
    def test_release_from_within_the_critical_section_does_not_deadlock(
        self, mock_remove
    ):
        """A signal handler fires on the thread that may already hold the lock."""
        done = threading.Event()

        def hold_then_release():
            # Built off the main thread : no signal handlers to restore, so this
            # exercises the thread lock only (signal.signal is main-thread only).
            lock = Lock()
            lock._has_created_lock = True
            # Without this, a reverted (non-reentrant) lock.py wedges this thread
            # while still holding the lock, and the atexit hook then blocks the
            # interpreter forever on exit instead of letting the test fail.
            atexit.unregister(lock.release)
            with lock._thread_lock:
                lock.release()
            done.set()

        worker = threading.Thread(target=hold_then_release, daemon=True)
        worker.start()
        assert done.wait(timeout=5), "release() deadlocked on its own thread lock"

    @patch("codecarbon.lock.open", new_callable=mock_open)
    def test_failed_acquire_leaves_the_handlers_alone(self, mock_file):
        # Another instance already holds the lock: stop() returns early and never
        # calls release(), so acquire() must not have taken the handlers at all.
        def sentinel(signum, frame):
            pass

        signal.signal(signal.SIGTERM, sentinel)
        mock_file.side_effect = FileExistsError
        lock = Lock()
        with self.assertRaises(FileExistsError):
            lock.acquire()

        self.assertIs(signal.getsignal(signal.SIGTERM), sentinel)
        self.assertIs(
            signal.getsignal(signal.SIGINT), self.original_handlers[signal.SIGINT]
        )


if __name__ == "__main__":
    unittest.main()
