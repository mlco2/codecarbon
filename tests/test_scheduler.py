import threading
import time
import unittest
from unittest import mock

from codecarbon.external import scheduler as scheduler_module
from codecarbon.external.scheduler import PeriodicScheduler
from tests.testutils import FakeClock

# Fake seconds: time only moves when a test calls clock.advance().
INTERVAL = 1.0
# Real seconds a negative check waits for something that must not happen. It
# only bounds the wait: a correct scheduler passes however slow the machine.
NEVER = 0.1


class TestPeriodicScheduler(unittest.TestCase):
    def make_scheduler(self, function, interval=INTERVAL):
        scheduler = PeriodicScheduler(interval, function)
        self.clock = scheduler.clock = FakeClock()
        self.addCleanup(scheduler.stop)
        return scheduler

    def test_ticks_run_on_a_single_thread(self):
        """Regression guard: one long-lived thread, not one thread per tick."""
        names = []
        scheduler = self.make_scheduler(
            lambda: names.append(threading.current_thread().name)
        )
        scheduler.start()
        for _ in range(5):
            self.clock.advance(INTERVAL)
        scheduler.stop()
        self.assertEqual(len(names), 5)
        self.assertEqual(len(set(names)), 1, f"expected one worker, got {names}")

    def test_slow_function_is_never_re_entered(self):
        """A function slower than the interval must not overlap with itself."""
        state = {"in_flight": 0, "overlaps": 0, "calls": 0}

        def slow():
            state["calls"] += 1
            state["in_flight"] += 1
            if state["in_flight"] > 1:
                state["overlaps"] += 1
            self.clock.sleep(INTERVAL * 2.4)
            state["in_flight"] -= 1

        scheduler = self.make_scheduler(slow)
        scheduler.start()
        for _ in range(20):
            self.clock.advance(INTERVAL / 4)
        scheduler.stop()
        self.assertGreater(state["calls"], 1)
        self.assertEqual(state["overlaps"], 0)

    def test_overrunning_call_waits_for_the_next_slot(self):
        """A call longer than the interval skips the missed slots, not the wait."""
        starts = []

        def slow():
            starts.append(self.clock.monotonic())
            self.clock.sleep(INTERVAL * 2.5)

        scheduler = self.make_scheduler(slow)
        scheduler.start()
        # The first slot is 4 steps away, then each 2.5 s call leaves half an
        # interval, 2 steps, before the next free slot.
        for _ in range(10):
            self.clock.advance(INTERVAL / 4)
        scheduler.stop()
        self.assertEqual(starts, [1.0, 4.0, 7.0, 10.0])

    def test_cadence_does_not_drift(self):
        """Deadlines are absolute: the time a call takes is not added to them."""
        starts = []

        def takes_a_while():
            starts.append(self.clock.monotonic())
            self.clock.sleep(INTERVAL * 0.5)

        scheduler = self.make_scheduler(takes_a_while)
        scheduler.start()
        for _ in range(10):
            self.clock.advance(INTERVAL / 4)
        scheduler.stop()
        self.assertEqual(starts, [1.0, 2.0, 3.0, 4.0])

    def test_stop_is_final(self):
        calls = []
        scheduler = self.make_scheduler(lambda: calls.append(1))
        scheduler.start()
        thread = scheduler._thread
        self.assertTrue(self.clock.wait_parked())
        scheduler.stop()
        self.assertTrue(scheduler._stopped)
        self.assertFalse(thread.is_alive(), "stop() returned before the loop ended")
        self.assertIsNone(scheduler._thread)
        self.clock.sleep(INTERVAL * 10)
        self.assertEqual(calls, [])

    def test_stop_before_start_and_double_stop_do_not_raise(self):
        scheduler = self.make_scheduler(lambda: None)
        scheduler.stop()
        scheduler.start()
        scheduler.stop()
        scheduler.stop()
        self.assertTrue(scheduler._stopped)

    def test_start_is_idempotent_and_restartable(self):
        calls = []
        scheduler = self.make_scheduler(lambda: calls.append(1))
        scheduler.start()
        first = scheduler._thread
        scheduler.start()
        self.assertIs(scheduler._thread, first, "start() armed a second thread")
        self.clock.advance(INTERVAL)
        scheduler.stop()
        self.assertFalse(first.is_alive())
        self.assertEqual(len(calls), 1)

        scheduler.start()
        second = scheduler._thread
        self.clock.advance(INTERVAL)
        scheduler.stop()
        self.assertEqual(len(calls), 2, "restart did not resume ticking")
        self.assertFalse(second.is_alive())

    @mock.patch.object(scheduler_module, "STOP_JOIN_TIMEOUT_SECONDS", 0.01)
    def test_start_after_a_timed_out_stop_resumes_without_overlap(self):
        """A restart during a wedged callback waits for it, then ticks again."""
        release = threading.Event()
        blocked_once = threading.Event()
        threads = []

        def wedged():
            threads.append(threading.current_thread())
            if not blocked_once.is_set():
                blocked_once.set()
                release.wait(5)

        scheduler = self.make_scheduler(wedged)
        scheduler.start()
        first = scheduler._thread
        self.clock.advance(INTERVAL, settle=False)
        self.assertTrue(blocked_once.wait(2), "callback never ran")

        with self.assertLogs("codecarbon", level="WARNING"):
            scheduler.stop()  # join times out, callback still blocked
        self.assertTrue(first.is_alive())
        self.assertIs(scheduler._thread, first, "stop() dropped the wedged thread")

        scheduler.start()  # must not be refused
        second = scheduler._thread
        self.assertIsNot(second, first)
        self.assertFalse(scheduler._stopped)
        self.assertFalse(
            self.clock.wait_parked(NEVER), "the new loop runs during the old call"
        )

        release.set()
        first.join(2)
        self.assertFalse(first.is_alive(), "the wedged thread never exited")
        self.clock.advance(INTERVAL)
        scheduler.stop()
        self.assertEqual(threads, [first, second])

    @mock.patch.object(scheduler_module, "STOP_JOIN_TIMEOUT_SECONDS", 0.01)
    def test_stop_from_the_callback_then_start_does_not_overlap(self):
        """stop() called by the callback itself must not let start() overlap it."""
        release = threading.Event()
        stopped_itself = threading.Event()
        threads = []

        def stops_itself():
            threads.append(threading.current_thread())
            if not stopped_itself.is_set():
                scheduler.stop()
                stopped_itself.set()
                release.wait(5)

        scheduler = self.make_scheduler(stops_itself)
        scheduler.start()
        first = scheduler._thread
        self.clock.advance(INTERVAL, settle=False)
        self.assertTrue(stopped_itself.wait(2), "callback never ran")

        scheduler.start()
        second = scheduler._thread
        self.assertFalse(
            self.clock.wait_parked(NEVER), "the new loop runs during the old call"
        )

        release.set()
        first.join(2)
        self.clock.advance(INTERVAL)
        scheduler.stop()
        self.assertEqual(threads, [first, second])

    def test_concurrent_starts_arm_a_single_loop(self):
        """Two threads calling start() at once must not create two loops."""

        class SlowEvent(threading.Event):
            def __init__(self):
                time.sleep(NEVER)  # widen the check-then-act window
                super().__init__()

        def concurrent_start_target():
            pass

        scheduler = self.make_scheduler(concurrent_start_target)
        barrier = threading.Barrier(2)

        def start():
            barrier.wait()
            scheduler.start()

        with mock.patch.object(scheduler_module, "Event", SlowEvent):
            starters = [threading.Thread(target=start) for _ in range(2)]
            for starter in starters:
                starter.start()
            for starter in starters:
                starter.join()
        scheduler.stop()
        alive = [
            t.name
            for t in threading.enumerate()
            if t.name == "codecarbon-concurrent_start_target"
        ]
        self.assertEqual(alive, [], "a loop survived stop(): two loops were armed")

    def test_exception_does_not_kill_the_loop(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise ValueError("boom")

        scheduler = self.make_scheduler(flaky)
        scheduler.start()
        with self.assertLogs("codecarbon", level="ERROR"):
            self.clock.advance(INTERVAL)
        self.clock.advance(INTERVAL)
        scheduler.stop()
        self.assertEqual(len(calls), 2)
