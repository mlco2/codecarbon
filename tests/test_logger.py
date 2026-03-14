import logging
import os
import tempfile
import unittest

from codecarbon.external.logger import logger, set_logger_format


class TestSetLoggerFormat(unittest.TestCase):
    """Tests for issue #375 — set_logger_format() must not clear user-defined handlers."""

    def setUp(self):
        self._original_handlers = logger.handlers[:]

    def tearDown(self):
        logger.handlers = self._original_handlers

    def test_file_handler_preserved_after_set_logger_format(self):
        """A FileHandler added by the user must survive a call to set_logger_format()."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            fh = logging.FileHandler(tmp_path)
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)

            # set_logger_format() is called automatically inside EmissionsTracker.__init__
            # It must NOT remove the user's FileHandler
            set_logger_format()

            file_handlers = [
                h for h in logger.handlers
                if isinstance(h, logging.FileHandler)
            ]
            self.assertEqual(
                len(file_handlers),
                1,
                "FileHandler must survive a call to set_logger_format()",
            )
        finally:
            fh.close()
            os.unlink(tmp_path)

    def test_stream_handler_not_duplicated(self):
        """Calling set_logger_format() twice must not duplicate the StreamHandler."""
        set_logger_format()
        set_logger_format()

        stream_handlers = [
            h for h in logger.handlers
            if type(h) is logging.StreamHandler
        ]
        self.assertEqual(
            len(stream_handlers),
            1,
            "Only one StreamHandler should exist after two calls to set_logger_format()",
        )


if __name__ == "__main__":
    unittest.main()
