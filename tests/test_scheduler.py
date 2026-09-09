import threading
import time
import unittest

from codecarbon.external.scheduler import PeriodicScheduler

INTERVAL = 0.05


class TestPeriodicScheduler(unittest.TestCase):
    def test_ticks_run_on_a_single_thread(self):
        """Regression guard: one long-lived thread, not one thread per tick."""
        names = set()
        scheduler = PeriodicScheduler(
            INTERVAL, lambda: names.add(threading.current_thread().name)
        )
        scheduler.start()
        time.sleep(INTERVAL * 10)
        scheduler.stop()
        # A one-element set also proves at least one tick happened.
        self.assertEqual(len(names), 1, f"expected one worker thread, got {names}")

    def test_slow_function_is_never_re_entered(self):
        """A function slower than the interval must not overlap with itself."""
        state = {"in_flight": 0, "overlaps": 0, "calls": 0}

        def slow():
            state["calls"] += 1
            state["in_flight"] += 1
            if state["in_flight"] > 1:
                state["overlaps"] += 1
            time.sleep(INTERVAL * 2.4)
            state["in_flight"] -= 1

        scheduler = PeriodicScheduler(INTERVAL, slow)
        scheduler.start()
        time.sleep(INTERVAL * 20)
        scheduler.stop()
        self.assertGreater(state["calls"], 1)
        self.assertEqual(state["overlaps"], 0)

    def test_stop_is_prompt_and_final(self):
        calls = []
        scheduler = PeriodicScheduler(10.0, lambda: calls.append(1))
        scheduler.start()
        before = time.monotonic()
        scheduler.stop()
        self.assertLess(time.monotonic() - before, 1.0)
        self.assertTrue(scheduler._stopped)
        time.sleep(0.1)
        self.assertEqual(calls, [])

    def test_stop_before_start_and_double_stop_do_not_raise(self):
        scheduler = PeriodicScheduler(INTERVAL, lambda: None)
        scheduler.stop()
        scheduler.start()
        scheduler.stop()
        scheduler.stop()
        self.assertTrue(scheduler._stopped)

    def test_start_is_idempotent_and_restartable(self):
        calls = []
        scheduler = PeriodicScheduler(INTERVAL, lambda: calls.append(1))
        scheduler.start()
        first = scheduler._thread
        scheduler.start()
        self.assertIs(scheduler._thread, first, "start() armed a second thread")
        scheduler.stop()
        self.assertFalse(first.is_alive())
        stopped_at = len(calls)

        scheduler.start()
        second = scheduler._thread
        time.sleep(INTERVAL * 4)
        scheduler.stop()
        self.assertGreater(len(calls), stopped_at, "restart did not resume ticking")
        self.assertFalse(second.is_alive())

    def test_start_after_a_timed_out_stop_leaves_only_the_new_loop(self):
        """A wedged callback exits when released instead of ticking again."""
        release = threading.Event()
        idents = []
        blocked_once = threading.Event()

        def wedged():
            idents.append(threading.get_ident())
            if not blocked_once.is_set():
                blocked_once.set()
                release.wait(5)

        scheduler = PeriodicScheduler(INTERVAL, wedged)
        scheduler.start()
        first = scheduler._thread
        self.assertTrue(blocked_once.wait(2), "callback never ran")

        scheduler.stop()  # join times out, callback still blocked
        self.assertTrue(first.is_alive())

        scheduler.start()  # a new run, immediately, on its own event
        second = scheduler._thread
        self.assertIsNot(second, first)

        release.set()
        first.join(2)
        self.assertFalse(first.is_alive(), "the wedged thread never exited")

        time.sleep(INTERVAL * 6)
        scheduler.stop()
        self.assertEqual(
            set(idents[1:]), {second.ident}, f"the old loop kept ticking: {idents}"
        )

    def test_exception_does_not_kill_the_loop(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise ValueError("boom")

        scheduler = PeriodicScheduler(INTERVAL, flaky)
        scheduler.start()
        time.sleep(INTERVAL * 6)
        scheduler.stop()
        self.assertGreater(len(calls), 1)
