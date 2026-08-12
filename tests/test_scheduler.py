import threading
import time
import unittest

from codecarbon.external.scheduler import PeriodicScheduler


class TestPeriodicScheduler(unittest.TestCase):
    def test_stop_during_timer_firing_does_not_rearm(self):
        """stop() landing between the timer firing and _run rescheduling must win."""
        calls = []
        scheduler = PeriodicScheduler(0.05, calls.append, 1)
        gate = threading.Event()
        original_start = scheduler.start

        def gated_start(from_run=False):
            if from_run:
                gate.wait(2)
            return original_start(from_run=from_run)

        scheduler.start = gated_start
        original_start(from_run=False)
        time.sleep(0.2)  # the timer fired, _run is blocked before start()

        scheduler.stop()
        calls_at_stop = len(calls)
        gate.set()
        time.sleep(0.3)

        self.assertTrue(scheduler._stopped)
        self.assertEqual(calls_at_stop, len(calls))

    def test_stop_while_payload_is_running(self):
        """No further invocation once stop() returned, even mid-payload."""
        calls = []
        in_payload = threading.Event()

        def slow_payload():
            calls.append(1)
            in_payload.set()
            time.sleep(0.2)

        scheduler = PeriodicScheduler(0.01, slow_payload)
        scheduler.start()
        self.assertTrue(in_payload.wait(2))
        scheduler.stop()
        time.sleep(0.3)

        self.assertEqual(1, len(calls))

    def test_start_twice_arms_a_single_timer(self):
        scheduler = PeriodicScheduler(10, lambda: None)
        scheduler.start()
        timer = scheduler._timer
        scheduler.start()
        self.assertIs(timer, scheduler._timer)
        scheduler.stop()

    def test_stop_is_safe_before_start_and_twice(self):
        scheduler = PeriodicScheduler(10, lambda: None)
        scheduler.stop()
        scheduler.start()
        scheduler.stop()
        scheduler.stop()
