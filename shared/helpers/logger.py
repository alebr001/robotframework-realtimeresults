# helpers/logger.py
import logging

def setup_root_logging(level="info"):
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="[{asctime}] [{name}] [{levelname}] {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
        force=True
    )