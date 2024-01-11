import time

import codecarbon.core.cpu

try:
    from codecarbon.core.perf import Perf
except ImportError:
    Perf = None


def test_perf():
    if codecarbon.core.cpu.is_perf_available() is False:
        return
    x = Perf(["energy-pkg"])
    x.start()
    time.sleep(20)
    x.delta(20.0)
    time.sleep(10)
    x.delta(10.0)
    x.stop()
