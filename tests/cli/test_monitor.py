from types import SimpleNamespace

import pytest
import typer

from codecarbon.cli import monitor as monitor_module


class FakeTracker:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.stopped = 0
        self._conf = {"output_file": "emissions.csv"}

    def start(self):
        return None

    def stop(self):
        self.stopped += 1
        return 0.123


def test_run_and_monitor_requires_command(monkeypatch):
    monkeypatch.setattr(monitor_module, "EmissionsTracker", FakeTracker)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=[]))

    assert exc_info.value.exit_code == 1


def test_run_and_monitor_handles_missing_command(monkeypatch):
    class FakePopen:
        def __init__(self, command, text=True):
            raise FileNotFoundError

    monkeypatch.setattr(monitor_module, "EmissionsTracker", FakeTracker)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=["missing-command"]))

    assert exc_info.value.exit_code == 127


def test_run_and_monitor_handles_generic_exception(monkeypatch):
    class FakePopen:
        def __init__(self, command, text=True):
            raise RuntimeError("boom")

    monkeypatch.setattr(monitor_module, "EmissionsTracker", FakeTracker)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=["python"]))

    assert exc_info.value.exit_code == 1


def test_run_and_monitor_handles_keyboard_interrupt(monkeypatch):
    process_info = {"terminated": 0, "killed": 0}

    class FakePopen:
        def __init__(self, command, text=True):
            return None

        def wait(self, timeout=None):
            if timeout is None:
                raise KeyboardInterrupt
            raise monitor_module.subprocess.TimeoutExpired("cmd", timeout)

        def terminate(self):
            process_info["terminated"] += 1

        def kill(self):
            process_info["killed"] += 1

    monkeypatch.setattr(monitor_module, "EmissionsTracker", FakeTracker)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=["python"]))

    assert exc_info.value.exit_code == 130
    assert process_info["terminated"] == 1
    assert process_info["killed"] == 1
