# producers/metric_scraper/metric_scraper.py

import time
import psutil
import requests
import socket
import logging
from datetime import datetime, timezone
from shared.helpers.config_loader import load_config

config = load_config()

# Configuration
INGEST_HOST = config.get("ingest_backend_host", "127.0.0.1")
INGEST_PORT = config.get("ingest_backend_port", 8001)
INGEST_URL = f"http://{INGEST_HOST}:{INGEST_PORT}/log"

INTERVAL = 60  # seconds
HOSTNAME = socket.gethostname()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metric-scraper")

def collect_metrics():
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    mem_percent = memory.percent
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

def send_metrics(metrics):
    for metric in metrics:
        try:
            response = requests.post(INGEST_URL, json=metric)
            if response.status_code != 200:
                logger.warning(f"Failed to send metric: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error sending metric: {e}")

def main():
    logger.info(f"Starting metric scraper. Sending to {INGEST_URL}")
    while True:
        metrics = collect_metrics()
        send_metrics(metrics)
        logger.info(f"Sent metrics: {metrics}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()