# helpers/logger.py
import logging

def setup_logging(level="info"):
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="[{levelname}] {message}",
        style="{",
        force=True
    )