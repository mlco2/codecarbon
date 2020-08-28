# -*- coding: utf-8 -*-

# Copyright (C) 2020 [COMET-ML]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import sys

if sys.version_info >= (3, 4):
    from unittest.mock import Mock
else:
    from mock import Mock

DETAILS = {}

NVML_TEMPERATURE_GPU = 0
INIT_MOCK = Mock()


class NVMLError(Exception):
    pass


def nvmlInit():
    return INIT_MOCK()


def nvmlDeviceGetCount():
    return 2


def nvmlDeviceGetHandleByIndex(index):
    return "handle_%s" % index


def nvmlDeviceGetName(handle):
    return DETAILS[handle]["name"]


def nvmlDeviceGetUUID(handle):
    return DETAILS[handle]["uuid"]


def nvmlDeviceGetMemoryInfo(handle):
    return DETAILS[handle]["memory"]


def nvmlDeviceGetTemperature(handle, sensorType):
    assert sensorType is NVML_TEMPERATURE_GPU
    return DETAILS[handle]["temperature"]


def nvmlDeviceGetPowerUsage(handle):
    return DETAILS[handle]["power_usage"]


def nvmlDeviceGetEnforcedPowerLimit(handle):
    return DETAILS[handle]["power_limit"]


def nvmlDeviceGetUtilizationRates(handle):
    return DETAILS[handle]["utilization_rate"]


def nvmlDeviceGetComputeMode(handle):
    return DETAILS[handle]["compute_mode"]


def nvmlDeviceGetComputeRunningProcesses(handle):
    return DETAILS[handle]["compute_processes"]


def nvmlDeviceGetGraphicsRunningProcesses(handle):
    return DETAILS[handle]["graphics_processes"]
