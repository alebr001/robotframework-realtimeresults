# producers/metric_scraper/metric_scraper.py
"""
Collects basic host metrics and sends them to the ingest API
via the shared AsyncHttpSink.
"""

import asyncio
import socket
from datetime import datetime, timezone

import psutil
import logging

from shared.helpers.logger import setup_root_logging
from shared.helpers.config_loader import load_config
from shared.sinks.http import AsyncHttpSink

INTERVAL = 60  # seconds
HOSTNAME = socket.gethostname()

config = load_config()
setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("metric-scraper")


# --------------------------------------------------------------------------- #
# Metric collection helpers
# --------------------------------------------------------------------------- #
def collect_metrics():
    """
    Gather CPU and memory usage metrics.

    Returns a list[dict] so we can easily iterate and dispatch events.
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    mem_percent = psutil.virtual_memory().percent
    timestamp = datetime.now(timezone.utc).isoformat()

    return [
        {
            "timestamp": timestamp,
            "event_type": "metric",
            "metric_name": "cpu_percent",
            "value": cpu_percent,
            "unit": "%",
            "source": HOSTNAME,
        },
        {
            "timestamp": timestamp,
            "event_type": "metric",
            "metric_name": "memory_percent",
            "value": mem_percent,
            "unit": "%",
            "source": HOSTNAME,
        },
    ]



async def main():
    ingest_host = config.get("ingest_backend_host", "127.0.0.1")
    ingest_port = config.get("ingest_backend_port", 8001)
    endpoint = f"http://{ingest_host}:{ingest_port}"

    logger.info("Starting metric scraper. Ingest endpoint: %s", endpoint)

    # Create one sink instance; reuse it for all events
    sink = AsyncHttpSink(endpoint=endpoint, timeout=2.0)

    while True:
        metrics = collect_metrics()

        # Dispatch each metric via the sink (await to keep back‑pressure)
        for metric in metrics:
            await sink._async_handle_event(metric)  # uses dispatch_map internally

        logger.info("Sent metrics: %s", metrics)
        await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    # asyncio.run() ensures a clean event‑loop lifecycle
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Log tailer stopped by user.")
