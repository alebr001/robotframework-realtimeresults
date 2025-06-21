import os

LOG_FILE_PATH = os.environ.get("LOG_FILE_PATH", "../flask-logging-demo/single_file_app_pattern/app.log")
INGEST_ENDPOINT = os.environ.get("INGEST_ENDPOINT", "http://localhost:9000/log")
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", 1.0))
SOURCE_LABEL = os.environ.get("SOURCE_LABEL", "flask-app")