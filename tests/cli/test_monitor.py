import os
from types import SimpleNamespace

import pytest
import typer

from codecarbon.cli import monitor as monitor_module


class FakeTracker:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.stopped = 0
        self._conf = {"output_file": "emissions.csv"}
        self._output_handlers = [SimpleNamespace(save_file_path="emissions.csv")]

    def start(self):
        return None

    def stop(self):
        self.stopped += 1
        return 0.123


def _patch_trackers(monkeypatch, online_cls=FakeTracker, offline_cls=FakeTracker):
    monkeypatch.setattr("codecarbon.emissions_tracker.EmissionsTracker", online_cls)
    monkeypatch.setattr(
        "codecarbon.emissions_tracker.OfflineEmissionsTracker", offline_cls
    )


def test_run_and_monitor_requires_command(monkeypatch):
    _patch_trackers(monkeypatch)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=[]))

    assert exc_info.value.exit_code == 1


def test_run_and_monitor_strips_nested_monitor_prefix(monkeypatch):
    captured = {}

    class FakePopen:
        def __init__(self, command, text=True):
            captured["command"] = command

        def wait(self):
            return 0

    _patch_trackers(monkeypatch)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(
            SimpleNamespace(args=["monitor", "--", "echo", "hi"])
        )

    assert exc_info.value.exit_code == 0
    assert captured["command"] == ["echo", "hi"]


def test_run_and_monitor_handles_missing_command(monkeypatch):
    class FakePopen:
        def __init__(self, command, text=True):
            raise FileNotFoundError

    _patch_trackers(monkeypatch)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=["missing-command"]))

    assert exc_info.value.exit_code == 127


def test_run_and_monitor_handles_generic_exception(monkeypatch):
    class FakePopen:
        def __init__(self, command, text=True):
            raise RuntimeError("boom")

    _patch_trackers(monkeypatch)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=["python"]))

    assert exc_info.value.exit_code == 1


def test_run_and_monitor_uses_offline_tracker_when_offline_mode(monkeypatch):
    captured = {}

    class FakeOfflineTracker(FakeTracker):
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs
            super().__init__()

    class FakePopen:
        def __init__(self, command, text=True):
            pass

        def wait(self):
            return 0

    _patch_trackers(monkeypatch, offline_cls=FakeOfflineTracker)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(
            SimpleNamespace(args=["echo", "hi"]),
            offline=True,
            country_iso_code="FRA",
        )

    assert exc_info.value.exit_code == 0
    assert captured["kwargs"]["country_iso_code"] == "FRA"


def test_run_and_monitor_uses_online_tracker_by_default(monkeypatch):
    captured = {}

    class FakeOnlineTracker(FakeTracker):
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs
            super().__init__()

    class FakePopen:
        def __init__(self, command, text=True):
            pass

        def wait(self):
            return 0

    _patch_trackers(monkeypatch, online_cls=FakeOnlineTracker)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(
            SimpleNamespace(args=["echo", "hi"]),
            save_to_api=True,
        )

    assert exc_info.value.exit_code == 0
    assert captured["kwargs"]["tracking_mode"] == "process"
    assert captured["kwargs"]["save_to_api"] is True


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

    _patch_trackers(monkeypatch)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(monitor_module, "print", lambda *args, **kwargs: None)

    with pytest.raises(typer.Exit) as exc_info:
        monitor_module.run_and_monitor(SimpleNamespace(args=["python"]))

    assert exc_info.value.exit_code == 130
    assert process_info["terminated"] == 1
    assert process_info["killed"] == 1


def _run_and_capture(monkeypatch, capsys, handlers):
    class FakePopen:
        def __init__(self, command, text=True):
            pass

        def wait(self):
            return 0

    class FakeTrackerWithHandlers(FakeTracker):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._output_handlers = handlers

    _patch_trackers(monkeypatch, online_cls=FakeTrackerWithHandlers)
    monkeypatch.setattr(monitor_module.subprocess, "Popen", FakePopen)

    with pytest.raises(typer.Exit):
        monitor_module.run_and_monitor(SimpleNamespace(args=["echo", "hi"]))

    # rich wraps long lines to the terminal width, so strip all whitespace
    return "".join(capsys.readouterr().out.split())


def test_run_and_monitor_reports_output_dir(monkeypatch, capsys, tmp_path):
    save_file_path = os.path.join(str(tmp_path), "emissions.csv")
    out = _run_and_capture(
        monkeypatch, capsys, [SimpleNamespace(save_file_path=save_file_path)]
    )

    assert f"Savedto:{save_file_path}" in out


def test_run_and_monitor_reports_no_path_without_file_output(monkeypatch, capsys):
    out = _run_and_capture(monkeypatch, capsys, [SimpleNamespace()])

    assert "Savedto:" not in out
