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

    def test_overrunning_call_waits_for_the_next_slot(self):
        """A call longer than the interval skips the missed slots, not the wait."""
        interval = 0.1
        spans = []

        def slow():
            start = time.monotonic()
            time.sleep(interval * 2.5)
            spans.append((start, time.monotonic()))

        scheduler = PeriodicScheduler(interval, slow)
        scheduler.start()
        time.sleep(interval * 12)
        scheduler.stop()
        self.assertGreater(len(spans), 2)
        gaps = [nxt[0] - prev[1] for prev, nxt in zip(spans, spans[1:])]
        # The next slot is 0.5 interval after each call ends.
        self.assertGreater(min(gaps), interval * 0.2, f"back-to-back calls: {gaps}")

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

    def test_start_after_a_timed_out_stop_resumes_without_overlap(self):
        """A restart during a wedged callback waits for it, then ticks again."""
        release = threading.Event()
        in_flight = {"now": 0, "max": 0}
        threads = []
        blocked_once = threading.Event()

        def wedged():
            in_flight["now"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["now"])
            threads.append(threading.current_thread())
            if not blocked_once.is_set():
                blocked_once.set()
                release.wait(5)
            in_flight["now"] -= 1

        scheduler = PeriodicScheduler(INTERVAL, wedged)
        scheduler.start()
        first = scheduler._thread
        self.assertTrue(blocked_once.wait(2), "callback never ran")

        with self.assertLogs("codecarbon", level="WARNING"):
            scheduler.stop()  # join times out, callback still blocked
        self.assertTrue(first.is_alive())
        self.assertIs(scheduler._thread, first, "stop() dropped the wedged thread")

        before = time.monotonic()
        scheduler.start()  # must neither block nor be refused
        self.assertLess(time.monotonic() - before, INTERVAL)
        second = scheduler._thread
        self.assertIsNot(second, first)
        self.assertFalse(scheduler._stopped)

        time.sleep(INTERVAL * 3)
        self.assertEqual(threads, [first], "the new loop ran during the old call")

        release.set()
        first.join(2)
        self.assertFalse(first.is_alive(), "the wedged thread never exited")
        time.sleep(INTERVAL * 6)
        scheduler.stop()
        self.assertIn(second, threads, "the restarted loop never ticked")
        self.assertEqual(in_flight["max"], 1, "two loops ran the callback at once")

    def test_stop_from_the_callback_then_start_does_not_overlap(self):
        """stop() called by the callback itself must not let start() overlap it."""
        release = threading.Event()
        stopped_itself = threading.Event()
        in_flight = {"now": 0, "max": 0}
        threads = []

        def stops_itself():
            in_flight["now"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["now"])
            threads.append(threading.current_thread())
            if not stopped_itself.is_set():
                scheduler.stop()
                stopped_itself.set()
                release.wait(5)
            in_flight["now"] -= 1

        scheduler = PeriodicScheduler(INTERVAL, stops_itself)
        scheduler.start()
        first = scheduler._thread
        self.assertTrue(stopped_itself.wait(2), "callback never ran")

        scheduler.start()
        time.sleep(INTERVAL * 3)
        self.assertEqual(threads, [first], "the new loop ran during the old call")

        release.set()
        time.sleep(INTERVAL * 6)
        scheduler.stop()
        self.assertGreater(len(threads), 1, "the restarted loop never ticked")
        self.assertEqual(in_flight["max"], 1, "two loops ran the callback at once")

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
