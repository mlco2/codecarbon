import dataclasses
import json
import logging

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData


class LoggerOutput(BaseOutput):
    """
    Send emissions data to a logger
    """

    def __init__(self, logger, severity=logging.INFO):
        self.logger = logger
        self.logging_severity = severity

    def out(self, total: EmissionsData, delta: EmissionsData):
        try:
            payload = dataclasses.asdict(total)
            self.logger.log(self.logging_severity, msg=json.dumps(payload))
        except Exception as e:
            logger.error(e, exc_info=True)

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        self.out(total, delta)


class GoogleCloudLoggerOutput(LoggerOutput):
    """
    Send emissions data to GCP Cloud Logging
    """

    def out(self, total: EmissionsData, delta: EmissionsData):
        try:
            payload = dataclasses.asdict(total)
            self.logger.log_struct(payload, severity=self.logging_severity)
        except Exception as e:
            logger.error(e, exc_info=True)

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        self.out(total, delta)
