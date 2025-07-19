import pytest
from shared.helpers import logger
import logging

def test_setup_root_logging_info_level():
    logger.setup_root_logging("info")
    logging.getLogger("test").info("Test message")
    # No assert: just check no exception

def test_setup_root_logging_error_level():
    logger.setup_root_logging("error")
    logging.getLogger("test").error("Error message")
    # No assert: just check no exception
