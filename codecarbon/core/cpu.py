from logging import getLogger
import os
import shutil
import sys

logger = getLogger(__name__)


def is_powergadget_available():
    try:
        IntelPowerGadget()
        return True
    except Exception as e:
        logger.debug(
            f"Exception occurred while instantiating IntelPowerGadget : {e}",
            exc_info=True,
        )
        return False


class IntelPowerGadget:
    _osx_exec = "PowerLog"
    _osx_exec_backup = "/Applications/Intel Power Gadget/PowerLog"
    _windows_exec = "PowerLog.exe"
    _linux_exec = "power_gadget"

    def __init__(self, duration=1, resolution=100):
        self._system = sys.platform.lower()
        self.duration = duration
        self.resolution = resolution
        self.cli = None

        if self._system.startswith("linux"):
            if shutil.which(IntelPowerGadget._linux_exec):
                self.cli = IntelPowerGadget._linux_exec
            else:
                raise Exception(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        elif self._system.startswith("windows"):
            if shutil.which(IntelPowerGadget._windows_exec):
                self.cli = IntelPowerGadget._windows_exec
            else:
                raise Exception(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        elif self._system.startswith("darwin"):
            if shutil.which(IntelPowerGadget._osx_exec):
                self.cli = IntelPowerGadget._osx_exec
            elif shutil.which(IntelPowerGadget._osx_exec_backup):
                self.cli = IntelPowerGadget._osx_exec_backup
            else:
                raise Exception(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        else:
            raise Exception("Platform not supported by Intel Power Gadget")
